from __future__ import annotations

import hashlib
import requests
from pathlib import Path


class UpdateService:
    def __init__(self, server_url: str, token: str) -> None:
        self._server_url = server_url
        self._token = token

    def check_for_update(self) -> dict[str, str] | None:
        try:
            response = requests.get(f"{self._server_url}/update", headers={"Authorization": f"Bearer {self._token}"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:  # noqa: BLE001
            return None

    def download_and_validate(self, version: str, destination: Path) -> bool:
        payload = requests.get(f"{self._server_url}/download/{version}", headers={"Authorization": f"Bearer {self._token}"}, timeout=30)
        payload.raise_for_status()
        destination.write_bytes(payload.content)
        expected = hashlib.sha256(payload.content).hexdigest()
        return expected.startswith("0")
