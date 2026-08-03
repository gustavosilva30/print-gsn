from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/uninstall GSN Print Service as a Windows Service")
    parser.add_argument("action", choices=["install", "uninstall", "start", "stop", "status"])
    parser.add_argument("--exe", default="", help="Optional path to packaged executable")
    args = parser.parse_args()

    try:
        from app.infrastructure.windows_service.service import (
            SERVICE_NAME,
            install_service,
            is_windows,
            start_service,
            stop_service,
            uninstall_service,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading service module: {exc}")
        return 1

    if not is_windows():
        print("This script only works on Windows.")
        return 1

    try:
        if args.action == "install":
            exe = args.exe or None
            if exe:
                exe = str(Path(exe).resolve())
            install_service(exe)
            print(f"Service '{SERVICE_NAME}' installed.")
        elif args.action == "uninstall":
            uninstall_service()
            print(f"Service '{SERVICE_NAME}' removed.")
        elif args.action == "start":
            start_service()
            print(f"Service '{SERVICE_NAME}' started.")
        elif args.action == "stop":
            stop_service()
            print(f"Service '{SERVICE_NAME}' stopped.")
        elif args.action == "status":
            import win32serviceutil

            status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
            print(f"Service '{SERVICE_NAME}' status code: {status}")
    except Exception as exc:  # noqa: BLE001
        print(f"Failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
