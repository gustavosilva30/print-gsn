from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlparse

from loguru import logger

from app.config.settings import Settings
from app.domain.job import PrintJob
from app.services.label_builder import LabelBuilder
from app.services.print_manager import PrinterManager


class CRMPrintBridge:
    """HTTP bridge compatible with CRM `mobile-estoque` raw_print_server.

    Endpoints:
      GET  /ping   -> { ok, printer }
      POST /print  -> { sku, nome, localizacao, condicao, marca?, modelo? }
      GET  /health -> { status }
    """

    def __init__(
        self,
        settings: Settings,
        printer_manager: PrinterManager | None = None,
        on_job: Callable[[PrintJob], None] | None = None,
    ) -> None:
        self._settings = settings
        self._printer_manager = printer_manager or PrinterManager(base_dir=settings.base_dir)
        self._on_job = on_job
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    @property
    def port(self) -> int:
        return int(getattr(self._settings, "local_http_port", 5555) or 5555)

    def start(self) -> None:
        if self._running:
            return
        host = str(getattr(self._settings, "local_http_host", "0.0.0.0") or "0.0.0.0")
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:
                logger.info("[local-http] " + (fmt % args))

            def _send_json(self, code: int, data: dict[str, Any]) -> None:
                body = json.dumps(data, ensure_ascii=True).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path == "/ping":
                    self._send_json(
                        200,
                        {
                            "ok": True,
                            "printer": bridge._settings.default_printer or "Argox OS-214 Plus",
                            "service": "gsn-print-service",
                            "mock_mode": bridge._settings.mock_mode,
                        },
                    )
                    return
                if path in {"/health", "/"}:
                    self._send_json(200, {"status": "ok", "service": "gsn-print-service"})
                    return
                self._send_json(404, {"error": "Not found"})

            def do_POST(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path != "/print":
                    self._send_json(404, {"error": "Not found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length) if length else b"{}"
                    data = json.loads(body.decode("utf-8") or "{}")
                    result = bridge.handle_print(data)
                    self._send_json(200, result)
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "JSON inválido"})
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Local HTTP print failed: {exc}", exc=exc)
                    self._send_json(500, {"error": str(exc)})

        self._server = ThreadingHTTPServer((host, self.port), Handler)
        self._running = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="local-http")
        self._thread.start()
        logger.info("Local HTTP print bridge listening on {host}:{port}", host=host, port=self.port)

    def stop(self) -> None:
        self._running = False
        if self._server is not None:
            try:
                self._server.shutdown()
            except Exception:  # noqa: BLE001
                pass
            self._server = None

    def handle_print(self, data: dict[str, Any]) -> dict[str, Any]:
        sku = str(data.get("sku", "S/N"))
        nome = str(data.get("nome", "Peça sem nome"))
        localizacao = str(data.get("localizacao", ""))
        condicao = str(data.get("condicao", "Usado"))
        marca = str(data.get("marca", ""))
        modelo = str(data.get("modelo", ""))
        copies = max(1, int(data.get("copies", 1) or 1))

        builder = LabelBuilder(dpi=int(getattr(self._settings, "argox_dpi", 203) or 203))
        payload = builder.build_estoque_crm(
            sku=sku,
            nome=nome,
            localizacao=localizacao,
            condicao=condicao,
            marca=marca,
            modelo=modelo,
            width_mm=int(getattr(self._settings, "paper_width", 50) or 50),
            height_mm=min(int(getattr(self._settings, "paper_height", 25) or 25), 30),
        )

        job = PrintJob(
            printer_name=self._settings.default_printer or "Argox OS-214 Plus",
            template="estoque_crm",
            payload={
                "raw": payload.decode("ascii", errors="replace"),
                "sku": sku,
                "nome": nome,
                "localizacao": localizacao,
                "condicao": condicao,
                "marca": marca,
                "modelo": modelo,
            },
            copies=copies,
            metadata={"source": "crm-local-http"},
        )
        if self._on_job is not None:
            self._on_job(job)

        self._printer_manager.print_job(
            job,
            mock=self._settings.mock_mode,
            default_printer=self._settings.default_printer,
            printer_type=self._settings.printer_type,
            paper_width=self._settings.paper_width,
            paper_height=self._settings.paper_height,
            command_language="PPLA",
            argox_model=getattr(self._settings, "argox_model", "OS-214 Plus"),
            argox_dpi=getattr(self._settings, "argox_dpi", 203),
            argox_darkness=getattr(self._settings, "argox_darkness", 10),
            argox_speed=getattr(self._settings, "argox_speed", 3),
        )
        logger.info("CRM local print OK sku={sku} mock={mock}", sku=sku, mock=self._settings.mock_mode)
        return {"ok": True, "sku": sku, "mock_mode": self._settings.mock_mode}
