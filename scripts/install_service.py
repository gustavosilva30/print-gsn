from __future__ import annotations

from pathlib import Path


if __name__ == "__main__":
    target = Path(r"C:\Program Files\GSN Print Service")
    target.mkdir(parents=True, exist_ok=True)
    print(f"Install directory ready: {target}")
