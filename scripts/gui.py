import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTS = Path(r"F:\PersonalRAG\knowledge_base\exports")


def run_cmd(cmd: List[str]) -> Tuple[int, str]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            shell=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return completed.returncode, output.strip()
    except Exception as exc:
        return 1, str(exc)


def open_path(path: Path) -> None:
    if path.exists():
        os.startfile(str(path))
    else:
        messagebox.showwarning("Not Found", f"Path does not exist: {path}")


def build_command(mode: str, job: str, keywords: str, write_drafts: bool, dry_run: bool, sort_by: str, threshold: str) -> List[str]:
    cmd = ["py", "-3", "-m", "app.main", mode]
    if mode == "jd":
        if job:
            cmd += ["--job", job]
        if keywords:
            cmd += ["--keywords"] + keywords.split()
        if write_drafts:
            cmd += ["--write-drafts"]
        if dry_run:
            cmd += ["--dry-run"]
        if sort_by:
            cmd += ["--sort-by", sort_by]
        if threshold:
            cmd += ["--threshold", threshold]
    else:
        if keywords:
            cmd += ["--keywords"] + keywords.split()
    return cmd


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RAG Desktop (Codex-style)")
        self.geometry("820x560")
        self.configure(bg="#0f1115")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0f1115")
        style.configure("TLabel", background="#0f1115", foreground="#e6e6e6")
        style.configure("TButton", background="#1e2330", foreground="#e6e6e6")
        style.configure("TCombobox", fieldbackground="#141823", background="#141823", foreground="#e6e6e6")
        style.configure("TEntry", fieldbackground="#141823", foreground="#e6e6e6")

        header = ttk.Label(self, text="Resume / Project RAG", font=("Consolas", 16, "bold"))
        header.pack(pady=(16, 8))

        container = ttk.Frame(self)
        container.pack(fill="x", padx=24)

        # Mode
        mode_row = ttk.Frame(container)
        mode_row.pack(fill="x", pady=6)
        ttk.Label(mode_row, text="Mode").pack(side="left", padx=(0, 12))
        self.mode = tk.StringVar(value="jd")
        mode_cb = ttk.Combobox(mode_row, textvariable=self.mode, values=["jd", "resume", "interview"], width=18)
        mode_cb.pack(side="left")

        # Job
        job_row = ttk.Frame(container)
        job_row.pack(fill="x", pady=6)
        ttk.Label(job_row, text="Job Name").pack(side="left", padx=(0, 12))
        self.job = tk.StringVar(value="RAG Assistant")
        ttk.Entry(job_row, textvariable=self.job, width=50).pack(side="left")

        # Keywords
        kw_row = ttk.Frame(container)
        kw_row.pack(fill="x", pady=6)
        ttk.Label(kw_row, text="Keywords").pack(side="left", padx=(0, 12))
        self.keywords = tk.StringVar(value="Python FastAPI RAG Retrieval")
        ttk.Entry(kw_row, textvariable=self.keywords, width=50).pack(side="left")

        # Options
        opt_row = ttk.Frame(container)
        opt_row.pack(fill="x", pady=6)
        self.write_drafts = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_row, text="write drafts", variable=self.write_drafts).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(opt_row, text="dry run", variable=self.dry_run).pack(side="left", padx=(0, 12))

        ttk.Label(opt_row, text="sort by").pack(side="left", padx=(16, 6))
        self.sort_by = tk.StringVar(value="updated")
        ttk.Combobox(opt_row, textvariable=self.sort_by, values=["updated", "keyword", "maturity"], width=12).pack(side="left")

        ttk.Label(opt_row, text="threshold").pack(side="left", padx=(16, 6))
        self.threshold = tk.StringVar(value="70")
        ttk.Entry(opt_row, textvariable=self.threshold, width=6).pack(side="left")

        # Command preview
        cmd_row = ttk.Frame(container)
        cmd_row.pack(fill="x", pady=(12, 6))
        ttk.Label(cmd_row, text="Command").pack(side="left", padx=(0, 12))
        self.cmd_preview = tk.StringVar(value="")
        ttk.Entry(cmd_row, textvariable=self.cmd_preview, width=70, state="readonly").pack(side="left")

        # Buttons
        btn_row = ttk.Frame(container)
        btn_row.pack(fill="x", pady=(10, 6))
        ttk.Button(btn_row, text="Run", command=self.on_run).pack(side="left", padx=(0, 12))
        ttk.Button(btn_row, text="Open Exports", command=lambda: open_path(EXPORTS)).pack(side="left")

        # Output
        out_label = ttk.Label(self, text="Output", font=("Consolas", 11, "bold"))
        out_label.pack(anchor="w", padx=24, pady=(16, 4))
        self.output = tk.Text(self, height=14, bg="#0f1115", fg="#d9d9d9", insertbackground="#ffffff")
        self.output.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self.update_preview()
        self.mode.trace_add("write", lambda *args: self.update_preview())
        self.job.trace_add("write", lambda *args: self.update_preview())
        self.keywords.trace_add("write", lambda *args: self.update_preview())
        self.write_drafts.trace_add("write", lambda *args: self.update_preview())
        self.dry_run.trace_add("write", lambda *args: self.update_preview())
        self.sort_by.trace_add("write", lambda *args: self.update_preview())
        self.threshold.trace_add("write", lambda *args: self.update_preview())

    def update_preview(self) -> None:
        cmd = build_command(
            self.mode.get(),
            self.job.get(),
            self.keywords.get(),
            self.write_drafts.get(),
            self.dry_run.get(),
            self.sort_by.get(),
            self.threshold.get(),
        )
        self.cmd_preview.set(" ".join(cmd))

    def on_run(self) -> None:
        cmd = build_command(
            self.mode.get(),
            self.job.get(),
            self.keywords.get(),
            self.write_drafts.get(),
            self.dry_run.get(),
            self.sort_by.get(),
            self.threshold.get(),
        )
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "Running...\n\n")
        code, out = run_cmd(cmd)
        self.output.insert(tk.END, out + "\n")
        if code == 0:
            self.output.insert(tk.END, "\n[OK] Done. Check exports folder.\n")
        else:
            self.output.insert(tk.END, f"\n[ERROR] Exit code {code}.\n")


if __name__ == "__main__":
    App().mainloop()
