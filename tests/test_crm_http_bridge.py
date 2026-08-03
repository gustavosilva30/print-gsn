from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from app.config.settings import Settings
from app.infrastructure.local_http.print_bridge import CRMPrintBridge
from app.services.label_builder import LabelBuilder
from app.services.print_manager import PrinterManager


def test_build_estoque_crm_matches_argox_classic() -> None:
    payload = LabelBuilder(dpi=203).build_estoque_crm(
        sku="35012",
        nome="Motor 1.0 Flex",
        localizacao="A-12-03",
        condicao="Usado",
        marca="VW",
        modelo="Gol",
    )
    text = payload.decode("ascii")
    assert text.startswith("n\n")
    assert "35012" in text
    assert "P 1" in text
    assert "Motor 1.0 Flex" in text


def test_crm_http_bridge_ping_and_print(tmp_path: Path) -> None:
    settings = Settings()
    settings.base_dir = tmp_path
    settings.mock_mode = True
    settings.local_http_enabled = True
    settings.local_http_host = "127.0.0.1"
    settings.local_http_port = 0  # will bind ephemeral - need override after

    # Pick free port
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    settings.local_http_port = port

    manager = PrinterManager(base_dir=tmp_path)
    bridge = CRMPrintBridge(settings=settings, printer_manager=manager)
    bridge.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=3) as resp:
            data = json.loads(resp.read().decode())
        assert data["ok"] is True

        body = json.dumps(
            {
                "sku": "35012",
                "nome": "Motor 1.0 Flex",
                "localizacao": "A-12-03",
                "condicao": "Usado",
                "marca": "VW",
                "modelo": "Gol",
            }
        ).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/print",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
        assert result["ok"] is True
        assert result["sku"] == "35012"
        ops = (tmp_path / "logs" / "printer_operations.log").read_text(encoding="utf-8")
        assert "success" in ops
    finally:
        bridge.stop()
