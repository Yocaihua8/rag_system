import os
from pathlib import Path
from tkinter import filedialog, Tk

from app.config import EXPORT_PATH


class Bridge:
    def pick_files(self):
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            files = filedialog.askopenfilenames()
            return list(files)
        finally:
            root.destroy()

    def pick_folder(self):
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            folder = filedialog.askdirectory()
            return folder
        finally:
            root.destroy()

    def open_path(self, path: str):
        target = Path(path)
        if not target.exists():
            return False
        try:
            os.startfile(str(target.resolve()))
            return True
        except OSError:
            return False

    def get_exports_path(self):
        return str(EXPORT_PATH.resolve())
