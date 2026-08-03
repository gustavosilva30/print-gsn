#!/usr/bin/env python3
"""Mock CRM WebSocket server for local homologation of GSN Print Service.

Usage:
  python tools/mock_websocket_server.py
  python tools/mock_websocket_server.py --host 127.0.0.1 --port 8765 --token demo-token

Then point config.json:
  "server_url": "ws://127.0.0.1:8765"
  "token": "demo-token"
  "mock_mode": true

Interactive commands (stdin):
  print   - send a sample print job to all connected clients
  ping    - send ping
  status  - list connected clients
  quit    - stop server
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install websockets: pip install websockets") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_envelope(
    message_type: str,
    *,
    token: str,
    computer_id: str = "server",
    company_id: str = "default-company",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "version": "1.0",
        "id": str(uuid4()),
        "timestamp": utc_now(),
        "type": message_type,
        "computer_id": computer_id,
        "company_id": company_id,
        "token": token,
        "payload": payload or {},
    }


class MockCRMServer:
    def __init__(self, host: str, port: int, token: str, auto_print: bool = False) -> None:
        self.host = host
        self.port = port
        self.token = token
        self.auto_print = auto_print
        self.clients: dict[WebSocketServerProtocol, dict[str, Any]] = {}
        self._print_counter = 0

    async def handler(self, websocket: WebSocketServerProtocol) -> None:
        peer = getattr(websocket, "remote_address", None)
        print(f"[+] client connected: {peer}")
        self.clients[websocket] = {"authenticated": False, "computer_id": "", "meta": {}}
        try:
            async for raw in websocket:
                await self._on_message(websocket, raw)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.pop(websocket, None)
            print(f"[-] client disconnected: {peer}")

    async def _on_message(self, websocket: WebSocketServerProtocol, raw: str | bytes) -> None:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[!] invalid JSON: {raw[:200]}")
            return

        msg_type = str(data.get("type", ""))
        computer_id = str(data.get("computer_id", ""))
        token = str(data.get("token", ""))
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}

        print(f"[<] type={msg_type} id={data.get('id')} computer={computer_id}")

        if token != self.token:
            print(f"[!] token mismatch from {computer_id}")

        info = self.clients.get(websocket)
        if info is not None:
            info["computer_id"] = computer_id
            info["meta"] = payload

        if msg_type == "auth":
            if info is not None:
                info["authenticated"] = True
            print(f"[*] authenticated computer_id={computer_id} name={payload.get('computer_name')}")
            if self.auto_print:
                await asyncio.sleep(0.5)
                await self.send_print(websocket, computer_id)
            return

        if msg_type in {"heartbeat", "ack", "completed", "failed", "status", "pong"}:
            if msg_type == "completed":
                print(f"[OK] job completed: {payload}")
            elif msg_type == "failed":
                print(f"[FAIL] job failed: {payload}")
            elif msg_type == "ack":
                print(f"[ACK] {payload}")
            return

        print(f"[?] unhandled client message type={msg_type}")

    async def send_print(self, websocket: WebSocketServerProtocol, computer_id: str = "") -> None:
        self._print_counter += 1
        external_id = f"crm-mock-{self._print_counter:04d}"
        envelope = build_envelope(
            "print",
            token=self.token,
            computer_id=computer_id or "server",
            payload={
                "external_job_id": external_id,
                "printer_name": "Argox OS-214 Plus",
                "template": "default",
                "copies": 1,
                "content": {
                    "company": "GSN Mock",
                    "product": "Etiqueta Demo",
                    "codigo": f"SKU-{self._print_counter:04d}",
                    "ean": "7891234567895",
                    "preco": "19,90",
                    "descricao": "Produto de teste do mock server",
                },
            },
        )
        await websocket.send(json.dumps(envelope, ensure_ascii=True))
        print(f"[>] print sent external_job_id={external_id}")

    async def broadcast_print(self) -> None:
        if not self.clients:
            print("[!] no connected clients")
            return
        for ws, info in list(self.clients.items()):
            await self.send_print(ws, info.get("computer_id", ""))

    async def broadcast_ping(self) -> None:
        for ws, info in list(self.clients.items()):
            envelope = build_envelope(
                "ping",
                token=self.token,
                computer_id=info.get("computer_id", "server"),
                payload={"request_id": str(uuid4())},
            )
            await ws.send(json.dumps(envelope, ensure_ascii=True))
            print("[>] ping sent")

    def list_clients(self) -> None:
        if not self.clients:
            print("No clients connected")
            return
        for ws, info in self.clients.items():
            print(
                f" - {getattr(ws, 'remote_address', '?')} "
                f"auth={info.get('authenticated')} computer_id={info.get('computer_id')}"
            )


async def _stdin_commands(server: MockCRMServer) -> None:
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    print("Commands: print | ping | status | quit")
    while True:
        line = await reader.readline()
        if not line:
            await asyncio.sleep(0.2)
            continue
        cmd = line.decode("utf-8", errors="replace").strip().lower()
        if cmd in {"quit", "exit", "q"}:
            print("Stopping...")
            return
        if cmd == "print":
            await server.broadcast_print()
        elif cmd == "ping":
            await server.broadcast_ping()
        elif cmd in {"status", "clients"}:
            server.list_clients()
        elif cmd:
            print(f"Unknown command: {cmd}")


async def run_server(host: str, port: int, token: str, auto_print: bool) -> None:
    server = MockCRMServer(host, port, token, auto_print=auto_print)
    async with websockets.serve(server.handler, host, port):
        print(f"Mock CRM WebSocket listening on ws://{host}:{port}")
        print(f"Expected token: {token}")
        print("Waiting for GSN Print Service clients...")
        try:
            await _stdin_commands(server)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock CRM WebSocket server for GSN Print Service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default="demo-token")
    parser.add_argument(
        "--auto-print",
        action="store_true",
        help="Send a sample print job automatically after client auth",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run_server(args.host, args.port, args.token, args.auto_print))
    except KeyboardInterrupt:
        print("\nStopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
