from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    server_url: str = os.getenv("GSN_SERVER_URL", "https://localhost")
    token: str = os.getenv("GSN_TOKEN", "demo-token")
    computer_name: str = os.getenv("GSN_COMPUTER_NAME", "GSN-PRINT")
    heartbeat_interval_seconds: int = int(os.getenv("GSN_HEARTBEAT_INTERVAL", "30"))
    auto_reconnect: bool = os.getenv("GSN_AUTO_RECONNECT", "true").lower() == "true"
    debug: bool = os.getenv("GSN_DEBUG", "true").lower() == "true"
    base_dir: Path = Path(__file__).resolve().parents[1]

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
