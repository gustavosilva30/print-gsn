from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(slots=True)
class Settings:
    server_url: str = os.getenv("GSN_SERVER_URL", "https://localhost")
    token: str = os.getenv("GSN_TOKEN", "demo-token")
    protocol_version: str = os.getenv("GSN_PROTOCOL_VERSION", "1.0")
    company_id: str = os.getenv("GSN_COMPANY_ID", "default-company")
    computer_name: str = os.getenv("GSN_COMPUTER_NAME", "GSN-PRINT")
    computer_id: str = os.getenv("GSN_COMPUTER_ID", "")
    heartbeat_interval_seconds: int = int(os.getenv("GSN_HEARTBEAT_INTERVAL", "30"))
    connect_timeout_seconds: int = int(os.getenv("GSN_CONNECT_TIMEOUT", "5"))
    read_timeout_seconds: int = int(os.getenv("GSN_READ_TIMEOUT", "2"))
    auto_reconnect: bool = os.getenv("GSN_AUTO_RECONNECT", "true").lower() == "true"
    reconnect_initial_delay_seconds: int = int(os.getenv("GSN_RECONNECT_INITIAL_DELAY", "1"))
    reconnect_max_delay_seconds: int = int(os.getenv("GSN_RECONNECT_MAX_DELAY", "30"))
    reconnect_multiplier: float = float(os.getenv("GSN_RECONNECT_MULTIPLIER", "2.0"))
    max_pending_outbound_messages: int = int(os.getenv("GSN_MAX_PENDING_OUTBOUND_MESSAGES", "1000"))
    service_version: str = os.getenv("GSN_SERVICE_VERSION", "0.1.0")
    debug: bool = os.getenv("GSN_DEBUG", "true").lower() == "true"
    mock_mode: bool = os.getenv("GSN_MOCK_MODE", "true").lower() == "true"
    enable_tray: bool = os.getenv("GSN_ENABLE_TRAY", "false").lower() == "true"
    local_http_enabled: bool = os.getenv("GSN_LOCAL_HTTP", "true").lower() == "true"
    local_http_host: str = os.getenv("GSN_LOCAL_HTTP_HOST", "0.0.0.0")
    local_http_port: int = int(os.getenv("GSN_LOCAL_HTTP_PORT", "5555"))
    base_dir: Path = Path(__file__).resolve().parents[1]
    default_printer: str = ""
    printer_type: str = "Argox"
    label_language: str = "PT-BR"
    copies: int = 1
    paper_width: int = 80
    paper_height: int = 50
    command_language: str = "PPLB"
    argox_model: str = "OS-214 Plus"
    argox_dpi: int = 203
    argox_darkness: int = 10
    argox_speed: int = 3

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        config_path = self.base_dir / "config" / "config.json"
        data: dict[str, object] = {}
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.default_printer = str(data.get("default_printer", self.default_printer))
            self.printer_type = str(data.get("printer_type", self.printer_type))
            self.label_language = str(data.get("label_language", self.label_language))
            self.copies = int(data.get("copies", self.copies))
            self.paper_width = int(data.get("paper_width", self.paper_width))
            self.paper_height = int(data.get("paper_height", self.paper_height))
            self.command_language = str(data.get("command_language", self.command_language))
            self.argox_model = str(data.get("argox_model", self.argox_model))
            self.argox_dpi = int(data.get("argox_dpi", self.argox_dpi))
            self.argox_darkness = int(data.get("argox_darkness", self.argox_darkness))
            self.argox_speed = int(data.get("argox_speed", self.argox_speed))
            self.server_url = str(data.get("server_url", self.server_url))
            self.token = str(data.get("token", self.token))
            self.protocol_version = str(data.get("protocol_version", self.protocol_version))
            self.company_id = str(data.get("company_id", self.company_id))
            self.computer_name = str(data.get("computer_name", self.computer_name))
            self.computer_id = str(data.get("computer_id", self.computer_id))
            self.heartbeat_interval_seconds = int(data.get("heartbeat_interval_seconds", self.heartbeat_interval_seconds))
            self.connect_timeout_seconds = int(data.get("connect_timeout_seconds", self.connect_timeout_seconds))
            self.read_timeout_seconds = int(data.get("read_timeout_seconds", self.read_timeout_seconds))
            self.auto_reconnect = self._as_bool(data.get("auto_reconnect", self.auto_reconnect))
            self.reconnect_initial_delay_seconds = int(
                data.get("reconnect_initial_delay_seconds", self.reconnect_initial_delay_seconds)
            )
            self.reconnect_max_delay_seconds = int(
                data.get("reconnect_max_delay_seconds", self.reconnect_max_delay_seconds)
            )
            self.reconnect_multiplier = float(data.get("reconnect_multiplier", self.reconnect_multiplier))
            self.max_pending_outbound_messages = int(
                data.get("max_pending_outbound_messages", self.max_pending_outbound_messages)
            )
            self.service_version = str(data.get("service_version", self.service_version))
            self.debug = self._as_bool(data.get("debug", self.debug))
            self.mock_mode = self._as_bool(data.get("mock_mode", self.mock_mode))
            self.enable_tray = self._as_bool(data.get("enable_tray", self.enable_tray))
            self.local_http_enabled = self._as_bool(data.get("local_http_enabled", self.local_http_enabled))
            self.local_http_host = str(data.get("local_http_host", self.local_http_host))
            self.local_http_port = int(data.get("local_http_port", self.local_http_port))
        if not self.computer_id:
            self.computer_id = str(uuid4())
            self._save_config(config_path, data)

    def _save_config(self, config_path: Path, original_data: dict[str, object]) -> None:
        config_data = dict(original_data)
        config_data.update(
            {
                "default_printer": self.default_printer,
                "printer_type": self.printer_type,
                "label_language": self.label_language,
                "copies": self.copies,
                "paper_width": self.paper_width,
                "paper_height": self.paper_height,
                "command_language": self.command_language,
                "argox_model": self.argox_model,
                "argox_dpi": self.argox_dpi,
                "argox_darkness": self.argox_darkness,
                "argox_speed": self.argox_speed,
                "server_url": self.server_url,
                "token": self.token,
                "protocol_version": self.protocol_version,
                "company_id": self.company_id,
                "computer_name": self.computer_name,
                "computer_id": self.computer_id,
                "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
                "connect_timeout_seconds": self.connect_timeout_seconds,
                "read_timeout_seconds": self.read_timeout_seconds,
                "auto_reconnect": self.auto_reconnect,
                "reconnect_initial_delay_seconds": self.reconnect_initial_delay_seconds,
                "reconnect_max_delay_seconds": self.reconnect_max_delay_seconds,
                "reconnect_multiplier": self.reconnect_multiplier,
                "max_pending_outbound_messages": self.max_pending_outbound_messages,
                "service_version": self.service_version,
                "debug": self.debug,
                "mock_mode": self.mock_mode,
                "enable_tray": self.enable_tray,
                "local_http_enabled": self.local_http_enabled,
                "local_http_host": self.local_http_host,
                "local_http_port": self.local_http_port,
            }
        )
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as handle:
            json.dump(config_data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")

    def _as_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)
