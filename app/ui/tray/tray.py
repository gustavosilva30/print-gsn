from __future__ import annotations

import tkinter as tk


class TrayWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GSN Print Service")
        self.root.geometry("300x200")
        self.root.withdraw()

    def run(self) -> None:
        self.root.mainloop()
