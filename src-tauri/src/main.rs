#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    net::{Ipv4Addr, TcpListener},
    sync::Mutex,
};

use serde::Serialize;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, State, WebviewWindow, WindowEvent,
};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

struct BackendSidecar {
    child: Mutex<Option<CommandChild>>,
    bootstrap: Mutex<Option<BackendBootstrap>>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendBootstrap {
    api_base_url: String,
    desktop_token: Option<String>,
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendSidecar {
            child: Mutex::new(None),
            bootstrap: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![backend_bootstrap])
        .setup(|app| {
            start_backend_sidecar(&app.handle())?;
            setup_tray(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() != "main" {
                return;
            }
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .run(tauri::generate_context!())
        .expect("failed to run Knowledge Island desktop shell");
}

fn start_backend_sidecar(app: &tauri::AppHandle) -> Result<(), String> {
    let secure_runtime = secure_runtime_enabled();
    let (bootstrap, port) = if secure_runtime {
        let port = reserve_loopback_port()?;
        (
            BackendBootstrap {
                api_base_url: format!("http://127.0.0.1:{port}"),
                desktop_token: Some(generate_desktop_token()?),
            },
            port,
        )
    } else {
        (
            BackendBootstrap {
                api_base_url: "http://127.0.0.1:8765".to_owned(),
                desktop_token: None,
            },
            8765,
        )
    };

    let mut sidecar = app
        .shell()
        .sidecar("knowledge-island-backend")
        .map_err(|error| error.to_string())?;
    if let Some(token) = bootstrap.desktop_token.as_deref() {
        sidecar = sidecar
            .env("KI_DESKTOP_MODE", "1")
            .env("KI_API_HOST", "127.0.0.1")
            .env("KI_API_PORT", port.to_string())
            .env("KI_DESKTOP_STARTUP_TOKEN", token);
    } else {
        // Prevent inherited desktop settings from silently changing the
        // current Vue/fixed-port production baseline.
        sidecar = sidecar.env("KI_DESKTOP_MODE", "0");
    }
    let (mut rx, child) = sidecar.spawn().map_err(|error| error.to_string())?;

    let state = app.state::<BackendSidecar>();
    *state.child.lock().map_err(|error| error.to_string())? = Some(child);
    *state.bootstrap.lock().map_err(|error| error.to_string())? = Some(bootstrap);

    let event_app = app.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    print!("{}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    eprint!("{}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Terminated(payload) => {
                    println!("Knowledge Island backend sidecar exited: {payload:?}");
                    clear_backend_state(&event_app);
                }
                _ => {}
            }
        }
    });

    Ok(())
}

#[tauri::command]
fn backend_bootstrap(
    window: WebviewWindow,
    state: State<'_, BackendSidecar>,
) -> Result<BackendBootstrap, String> {
    if window.label() != "main" {
        return Err("backend bootstrap is only available to the main window".to_owned());
    }
    state
        .bootstrap
        .lock()
        .map_err(|error| error.to_string())?
        .clone()
        .ok_or_else(|| "backend sidecar is not initialized".to_owned())
}

fn secure_runtime_enabled() -> bool {
    std::env::var("KI_TAURI_SECURE_RUNTIME")
        .map(|value| is_truthy(&value))
        .unwrap_or(false)
}

fn is_truthy(value: &str) -> bool {
    matches!(
        value.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on"
    )
}

fn reserve_loopback_port() -> Result<u16, String> {
    let listener =
        TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).map_err(|error| error.to_string())?;
    let port = listener
        .local_addr()
        .map_err(|error| error.to_string())?
        .port();
    drop(listener);
    Ok(port)
}

fn generate_desktop_token() -> Result<String, String> {
    let mut bytes = [0_u8; 32];
    getrandom::fill(&mut bytes).map_err(|error| error.to_string())?;
    Ok(bytes.iter().map(|byte| format!("{byte:02x}")).collect())
}

fn setup_tray(app: &tauri::App) -> tauri::Result<()> {
    let open = MenuItem::with_id(app, "open", "打开知识岛", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&open, &quit])?;

    let mut tray = TrayIconBuilder::new()
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "open" => show_main_window(app),
            "quit" => {
                kill_backend_sidecar(app);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main_window(&tray.app_handle());
            }
        });

    if let Some(icon) = app.default_window_icon() {
        tray = tray.icon(icon.clone());
    }

    tray.build(app)?;
    Ok(())
}

fn show_main_window(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn kill_backend_sidecar(app: &tauri::AppHandle) {
    let state = app.state::<BackendSidecar>();
    if let Ok(mut guard) = state.child.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    };
    if let Ok(mut guard) = state.bootstrap.lock() {
        *guard = None;
    };
}

fn clear_backend_state(app: &tauri::AppHandle) {
    let state = app.state::<BackendSidecar>();
    if let Ok(mut guard) = state.child.lock() {
        *guard = None;
    };
    if let Ok(mut guard) = state.bootstrap.lock() {
        *guard = None;
    };
}

#[cfg(test)]
mod tests {
    use super::{generate_desktop_token, is_truthy, reserve_loopback_port};

    #[test]
    fn secure_runtime_flag_only_accepts_explicit_truthy_values() {
        for value in ["1", "true", "TRUE", " yes ", "on"] {
            assert!(is_truthy(value));
        }
        for value in ["", "0", "false", "enabled", "localhost"] {
            assert!(!is_truthy(value));
        }
    }

    #[test]
    fn desktop_token_is_32_random_bytes_encoded_as_lowercase_hex() {
        let first = generate_desktop_token().expect("first token");
        let second = generate_desktop_token().expect("second token");

        assert_eq!(first.len(), 64);
        assert!(first.chars().all(|character| character.is_ascii_hexdigit()));
        assert_eq!(first, first.to_ascii_lowercase());
        assert_ne!(first, second);
    }

    #[test]
    fn reserved_backend_port_is_dynamic_and_nonzero() {
        let port = reserve_loopback_port().expect("loopback port");

        assert!(port > 0);
    }
}
