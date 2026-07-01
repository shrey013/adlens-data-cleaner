"""Entry point for the AdLens Data Cleaner desktop application."""
from __future__ import annotations

from gui import AdLensApp

def main() -> None:
    app = AdLensApp()
    app.mainloop()

if __name__ == "__main__":
    main()