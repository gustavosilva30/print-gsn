from __future__ import annotations

import datetime as dt
import platform
from dataclasses import dataclass

from app.infrastructure.printers.base import BasePrinter


@dataclass(frozen=True, slots=True)
class ArgoxModelProfile:
    """Hardware profile for an Argox thermal printer family."""

    model: str
    dpi: int
    max_width_mm: int
    default_speed: int
    default_darkness: int
    supports_ppla: bool = True
    supports_pplb: bool = True


# Known profiles used by GSN Print Service
ARGOX_PROFILES: dict[str, ArgoxModelProfile] = {
    "OS-214 Plus": ArgoxModelProfile(
        model="OS-214 Plus",
        dpi=203,
        max_width_mm=104,
        default_speed=3,
        default_darkness=10,
    ),
    "OS-214": ArgoxModelProfile(
        model="OS-214",
        dpi=203,
        max_width_mm=104,
        default_speed=3,
        default_darkness=10,
    ),
    "default": ArgoxModelProfile(
        model="Argox",
        dpi=203,
        max_width_mm=104,
        default_speed=3,
        default_darkness=10,
    ),
}


def resolve_argox_profile(model: str | None = None) -> ArgoxModelProfile:
    if not model:
        return ARGOX_PROFILES["OS-214 Plus"]
    key = model.strip()
    if key in ARGOX_PROFILES:
        return ARGOX_PROFILES[key]
    # Fuzzy match
    lowered = key.lower()
    for name, profile in ARGOX_PROFILES.items():
        if name.lower() in lowered or lowered in name.lower():
            return profile
    return ARGOX_PROFILES["default"]


class ArgoxPrinter(BasePrinter):
    """Argox thermal printer driver targeting OS-214 Plus (PPLA / PPLB / RAW).

    - mock=True: stores payloads and writes them under logs/mock_print_jobs
    - Windows + mock=False: sends bytes through the Win32 RAW spooler
    - Non-Windows + mock=False: persists payload for diagnostics (no hardware)
    """

    def __init__(
        self,
        name: str,
        mock: bool = False,
        *,
        model: str = "OS-214 Plus",
        dpi: int | None = None,
        darkness: int | None = None,
        speed: int | None = None,
        command_language: str = "PPLB",
    ) -> None:
        super().__init__(name, mock=mock)
        self.profile = resolve_argox_profile(model)
        self.model = self.profile.model
        self.dpi = dpi or self.profile.dpi
        self.darkness = darkness if darkness is not None else self.profile.default_darkness
        self.speed = speed if speed is not None else self.profile.default_speed
        self.command_language = (command_language or "PPLB").upper()

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def print_raw(self, payload: bytes) -> None:
        if not self._connected:
            raise RuntimeError("Printer is not connected")
        if not payload:
            raise ValueError("No payload provided")
        if self._mock:
            self._payloads.append(payload)
            self._save_mock_payload(payload)
            return
        if platform.system() != "Windows":
            self._payloads.append(payload)
            self._save_mock_payload(payload)
            return
        try:
            import win32print
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"win32print is not available: {exc}") from exc
        hprinter = win32print.OpenPrinter(self.name)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("GSN Print Argox", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, payload)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)

    def print_test(self) -> None:
        self.print_label(self.build_test_label())

    def print_label(self, payload: bytes | str | None = None) -> None:
        if not self._connected:
            raise RuntimeError("Printer is not connected")
        if payload is None:
            payload = self.build_test_label()
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.print_raw(payload)

    def status(self) -> str:
        return "Ready" if self._connected else "Disconnected"

    def build_test_label(self) -> bytes:
        """Build a self-test label in the configured command language."""
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.command_language == "PPLA":
            return self._build_ppla_test(now)
        return self._build_pplb_test(now)

    def _build_pplb_test(self, now: str) -> bytes:
        # PPLB on Argox OS-214 Plus is ZPL-II compatible over RAW
        width_dots = int(self.dpi * 2.0)  # ~50mm at 203 dpi ≈ 400 dots
        height_dots = int(self.dpi * 1.2)  # ~30mm
        lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            f"^PR{self.speed}",
            f"^MD{self.darkness}",
            "^FO20,20^A0N,28,28^FDGSN Print Service^FS",
            "^FO20,55^A0N,22,22^FDArgox Test Label^FS",
            f"^FO20,90^A0N,20,20^FDModel: {self.model}^FS",
            f"^FO20,120^A0N,18,18^FD{now}^FS",
            "^FO20,150^A0N,20,20^FDCode: TESTE001^FS",
            "^FO20,185^BY2^BCN,60,Y,N,N^FDTESTE001^FS",
            "^XZ",
        ]
        return "\n".join(lines).encode("utf-8")

    def _build_ppla_test(self, now: str) -> bytes:
        # Classic Argox/Datamax-style PPLA label for validation
        lines = [
            "I8,A,001",
            f"Q{self._mm_to_dots(30):04d},024",
            f"q{self._mm_to_dots(50)}",
            f"S{self.speed}",
            f"D{self.darkness}",
            "ZT",
            f'A50,30,0,3,1,1,N,"GSN Print Service"',
            f'A50,70,0,2,1,1,N,"Argox Test Label"',
            f'A50,100,0,2,1,1,N,"Model: {self.model}"',
            f'A50,130,0,2,1,1,N,"{now}"',
            f'A50,160,0,2,1,1,N,"Code: TESTE001"',
            "B50,200,0,1,2,2,60,B,\"TESTE001\"",
            "P1",
        ]
        return "\n".join(lines).encode("utf-8")

    def _mm_to_dots(self, mm: float) -> int:
        return max(1, int(round(mm * self.dpi / 25.4)))

    # Backwards-compatible alias used by older call sites
    def _build_test_label(self) -> str:
        return self.build_test_label().decode("utf-8", errors="ignore")
