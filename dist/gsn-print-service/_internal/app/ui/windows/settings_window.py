from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class SettingsWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Configurações")
        self.root.geometry("400x300")
        self.root.withdraw()

    def show(self) -> None:
        self.root.deiconify()
