from __future__ import annotations

import sys

from app.infrastructure.windows_service.service import (
    SERVICE_NAME,
    SERVICE_DISPLAY_NAME,
    is_windows,
)


def test_service_constants() -> None:
    assert SERVICE_NAME == "GSNPrintService"
    assert "GSN" in SERVICE_DISPLAY_NAME


def test_is_windows_matches_platform() -> None:
    assert is_windows() is sys.platform.startswith("win")


def test_install_service_rejected_on_non_windows() -> None:
    if is_windows():
        return
    from app.infrastructure.windows_service.service import install_service
    import pytest

    with pytest.raises(RuntimeError, match="Windows"):
        install_service()
