from __future__ import annotations

from types import SimpleNamespace

from Urban_Amenities2.ui import run


def test_main_uses_settings_and_runs_server(monkeypatch) -> None:
    settings = SimpleNamespace(host="0.0.0.0", port=8080, debug=False)

    monkeypatch.setattr(run.UISettings, "from_environment", classmethod(lambda cls: settings))

    captured = {}

    class DummyApp:
        def run_server(self, *, host: str, port: int, debug: bool) -> None:
            captured["host"] = host
            captured["port"] = port
            captured["debug"] = debug

    monkeypatch.setattr(run, "create_app", lambda cfg: DummyApp())

    run.main()

    assert captured == {"host": "0.0.0.0", "port": 8080, "debug": False}
