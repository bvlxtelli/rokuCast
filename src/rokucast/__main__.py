"""PyInstaller/uv-safe entry: `uv run rokucast` / `python -m rokucast`."""

from rokucast.app import main

if __name__ == "__main__":
    main()
