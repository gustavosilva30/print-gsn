from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.settings import Settings


class SettingsWindow:
    """Minimal configuration UI for first-run / tray access."""

    def __init__(self, settings: Settings | None = None) -> None:
        from app.config.settings import Settings as SettingsCls

        self._settings = settings or SettingsCls()
        self.root = tk.Tk()
        self.root.title("GSN Print Service — Configurações")
        self.root.geometry("480x420")
        self.root.resizable(False, False)

        self._vars: dict[str, tk.StringVar] = {
            "server_url": tk.StringVar(value=self._settings.server_url),
            "token": tk.StringVar(value=self._settings.token),
            "company_id": tk.StringVar(value=self._settings.company_id),
            "computer_name": tk.StringVar(value=self._settings.computer_name),
            "default_printer": tk.StringVar(value=self._settings.default_printer),
            "printer_type": tk.StringVar(value=self._settings.printer_type),
            "command_language": tk.StringVar(value=getattr(self._settings, "command_language", "PPLB")),
            "argox_model": tk.StringVar(value=getattr(self._settings, "argox_model", "OS-214 Plus")),
            "mock_mode": tk.StringVar(value="true" if self._settings.mock_mode else "false"),
        }
        self._build_form()

    def _build_form(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        rows = [
            ("URL do servidor (ws/wss)", "server_url"),
            ("Token", "token"),
            ("Company ID", "company_id"),
            ("Nome do computador", "computer_name"),
            ("Impressora padrão", "default_printer"),
            ("Tipo de impressora", "printer_type"),
            ("Linguagem (PPLB/PPLA)", "command_language"),
            ("Modelo Argox", "argox_model"),
            ("Mock mode (true/false)", "mock_mode"),
        ]
        for index, (label, key) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky=tk.W, pady=4)
            ttk.Entry(frame, textvariable=self._vars[key], width=42).grid(row=index, column=1, sticky=tk.EW, pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows), column=0, columnspan=2, pady=16)
        ttk.Button(buttons, text="Salvar", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Fechar", command=self.root.destroy).pack(side=tk.LEFT, padx=6)

    def show(self) -> None:
        self.root.deiconify()
        self.root.mainloop()

    def _save(self) -> None:
        config_path = self._settings.base_dir / "config" / "config.json"
        data: dict[str, object] = {}
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

        data["server_url"] = self._vars["server_url"].get().strip()
        data["token"] = self._vars["token"].get().strip()
        data["company_id"] = self._vars["company_id"].get().strip()
        data["computer_name"] = self._vars["computer_name"].get().strip()
        data["default_printer"] = self._vars["default_printer"].get().strip()
        data["printer_type"] = self._vars["printer_type"].get().strip() or "Argox"
        data["command_language"] = self._vars["command_language"].get().strip() or "PPLB"
        data["argox_model"] = self._vars["argox_model"].get().strip() or "OS-214 Plus"
        data["mock_mode"] = self._vars["mock_mode"].get().strip().lower() == "true"

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")

        # Reflect into live settings object (restart still recommended for WS URL)
        self._settings.server_url = str(data["server_url"])
        self._settings.token = str(data["token"])
        self._settings.company_id = str(data["company_id"])
        self._settings.computer_name = str(data["computer_name"])
        self._settings.default_printer = str(data["default_printer"])
        self._settings.printer_type = str(data["printer_type"])
        self._settings.command_language = str(data["command_language"])
        self._settings.argox_model = str(data["argox_model"])
        self._settings.mock_mode = bool(data["mock_mode"])

        messagebox.showinfo(
            "Configurações",
            "Configuração salva.\nReinicie o serviço para aplicar URL/token do WebSocket.",
        )
