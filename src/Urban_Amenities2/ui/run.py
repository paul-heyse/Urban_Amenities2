"""Entry point for running the Dash UI."""

from __future__ import annotations

from . import UISettings, create_app


def main() -> None:
    settings = UISettings.from_environment()
    app = create_app(settings)
    app.run_server(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
