import {
  Notice,
  PluginSettingTab,
  Setting,
  type App,
} from "obsidian";

import type { PluginState } from "./types";

export interface BridgeSettingsController {
  readonly state: PluginState;
  saveConfiguration(input: { backend_url?: string; output_root?: string }): Promise<void>;
  completePairing(code: string): Promise<void>;
  revokeConnection(): Promise<void>;
  synchronizeNow(): Promise<void>;
}

export class KnowledgeIslandSettingTab extends PluginSettingTab {
  private pairingCode = "";

  constructor(
    app: App,
    private readonly controller: BridgeSettingsController,
  ) {
    super(app, controller as never);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Knowledge Island Bridge" });
    containerEl.createEl("p", {
      text: "仅连接本机 Knowledge Island 服务。令牌保存在当前 Vault 的插件 data.json 中，不会写入笔记或 URL。",
    });

    new Setting(containerEl)
      .setName("本地服务地址")
      .setDesc("只接受 localhost、127.0.0.1 或 ::1 的 HTTP/HTTPS 地址。")
      .addText((text) => {
        text
          .setPlaceholder("http://127.0.0.1:8765")
          .setValue(this.controller.state.backend_url)
          .onChange(async (value) => {
            await this.controller.saveConfiguration({ backend_url: value });
          });
      });

    new Setting(containerEl)
      .setName("托管输出根")
      .setDesc("留空时使用主应用生成的 Knowledge Island/<项目名>；该目录及其子目录不会反向摄入。")
      .addText((text) => {
        text
          .setPlaceholder("Knowledge Island/项目名")
          .setValue(this.controller.state.output_root)
          .onChange(async (value) => {
            await this.controller.saveConfiguration({ output_root: value });
          });
      });

    if (this.controller.state.token) {
      this.renderConnectedSettings(containerEl);
    } else {
      this.renderPairingSettings(containerEl);
    }
  }

  private renderPairingSettings(containerEl: HTMLElement): void {
    new Setting(containerEl)
      .setName("一次性配对码")
      .setDesc("配对码由 Knowledge Island 主应用生成，限时且仅可使用一次。")
      .addText((text) => {
        text
          .setPlaceholder("输入配对码")
          .setValue(this.pairingCode)
          .onChange((value) => {
            this.pairingCode = value.trim();
          });
        text.inputEl.type = "password";
      })
      .addButton((button) => {
        button
          .setButtonText("完成配对")
          .setCta()
          .onClick(async () => {
            if (!this.pairingCode) {
              new Notice("请输入 Knowledge Island 配对码。");
              return;
            }
            button.setDisabled(true);
            try {
              await this.controller.completePairing(this.pairingCode);
              this.pairingCode = "";
              new Notice("Knowledge Island 配对成功，正在建立首次同步队列。");
              this.display();
            } catch (error) {
              new Notice(userFacingError(error, "配对失败"));
            } finally {
              button.setDisabled(false);
            }
          });
      });
  }

  private renderConnectedSettings(containerEl: HTMLElement): void {
    new Setting(containerEl)
      .setName("连接状态")
      .setDesc(
        `项目 ${this.controller.state.project_id}；连接 ${this.controller.state.connection_id}`,
      )
      .addButton((button) => {
        button
          .setButtonText("立即同步")
          .onClick(async () => {
            button.setDisabled(true);
            try {
              await this.controller.synchronizeNow();
              new Notice("Knowledge Island 同步已执行。");
            } catch (error) {
              new Notice(userFacingError(error, "同步失败"));
            } finally {
              button.setDisabled(false);
            }
          });
      })
      .addButton((button) => {
        button
          .setButtonText("撤销连接")
          .setWarning()
          .onClick(async () => {
            button.setDisabled(true);
            try {
              await this.controller.revokeConnection();
              new Notice("Knowledge Island 连接已撤销，本地离线队列已清除。");
              this.display();
            } catch (error) {
              new Notice(userFacingError(error, "撤销失败"));
            } finally {
              button.setDisabled(false);
            }
          });
      });
  }
}

function userFacingError(error: unknown, prefix: string): string {
  if (error instanceof Error && error.message) {
    return `${prefix}：${error.message}`;
  }
  return `${prefix}。`;
}
