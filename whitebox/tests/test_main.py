import importlib


def test_get_player_names_parses_and_filters(monkeypatch):
    main = importlib.import_module("main")
    monkeypatch.setattr("builtins.input", lambda _prompt: " Alice, , Bob ,  Cara  ")

    names = main.get_player_names()

    assert names == ["Alice", "Bob", "Cara"]


def test_main_runs_game_when_setup_is_valid(monkeypatch):
    main = importlib.import_module("main")
    called = {"run": False, "names": None}

    class FakeGame:
        def __init__(self, names):
            called["names"] = names

        def run(self):
            called["run"] = True

    monkeypatch.setattr(main, "get_player_names", lambda: ["Alice", "Bob"])
    monkeypatch.setattr(main, "Game", FakeGame)

    main.main()

    assert called["names"] == ["Alice", "Bob"]
    assert called["run"] is True


def test_main_handles_keyboard_interrupt(monkeypatch, capsys):
    main = importlib.import_module("main")

    class InterruptGame:
        def __init__(self, _names):
            pass

        def run(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(main, "get_player_names", lambda: ["Alice", "Bob"])
    monkeypatch.setattr(main, "Game", InterruptGame)

    main.main()

    out = capsys.readouterr().out
    assert "Game interrupted" in out


def test_main_handles_value_error(monkeypatch, capsys):
    main = importlib.import_module("main")

    class BrokenGame:
        def __init__(self, _names):
            raise ValueError("bad setup")

    monkeypatch.setattr(main, "get_player_names", lambda: ["Alice"])
    monkeypatch.setattr(main, "Game", BrokenGame)

    main.main()

    out = capsys.readouterr().out
    assert "Setup error: bad setup" in out
