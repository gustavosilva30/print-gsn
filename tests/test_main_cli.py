from __future__ import annotations

from app.main import build_parser


def test_parser_accepts_tray_and_service_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--tray"])
    assert args.tray is True
    args = parser.parse_args(["--headless"])
    assert args.headless is True
    args = parser.parse_args(["--install-service"])
    assert args.install_service is True
