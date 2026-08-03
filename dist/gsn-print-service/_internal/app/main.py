from __future__ import annotations

import argparse
import sys

from loguru import logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GSN Print Service")
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Run with system tray icon (recommended for interactive use)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without tray (default when not using --tray)",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Install as Windows Service (Windows + admin only)",
    )
    parser.add_argument(
        "--uninstall-service",
        action="store_true",
        help="Uninstall Windows Service (Windows + admin only)",
    )
    parser.add_argument(
        "--start-service",
        action="store_true",
        help="Start Windows Service",
    )
    parser.add_argument(
        "--stop-service",
        action="store_true",
        help="Stop Windows Service",
    )
    parser.add_argument(
        "--service",
        action="store_true",
        help="Host process for Windows Service Control Manager",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.install_service or args.uninstall_service or args.start_service or args.stop_service or args.service:
        from app.infrastructure.windows_service.service import (
            install_service,
            run_service_host,
            start_service,
            stop_service,
            uninstall_service,
        )

        if args.service:
            run_service_host()
            return 0
        if args.install_service:
            install_service()
            logger.info("Windows service installed")
            return 0
        if args.uninstall_service:
            uninstall_service()
            logger.info("Windows service uninstalled")
            return 0
        if args.start_service:
            start_service()
            logger.info("Windows service started")
            return 0
        if args.stop_service:
            stop_service()
            logger.info("Windows service stopped")
            return 0

    from app.application.application import Application
    from app.config.settings import Settings

    settings = Settings()
    app = Application(settings)

    # Prefer tray when requested, or when enable_tray is set in settings
    use_tray = args.tray or (getattr(settings, "enable_tray", False) and not args.headless)
    if use_tray:
        logger.info("Starting in tray mode")
        return app.run_with_tray()

    logger.info("Starting in headless mode")
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
