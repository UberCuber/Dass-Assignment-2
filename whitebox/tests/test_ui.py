from moneypoly.board import Board
from moneypoly.player import Player
from moneypoly import ui


def test_print_banner(capsys):
    ui.print_banner("Demo")
    out = capsys.readouterr().out

    assert "Demo" in out
    assert "=" * 10 in out


def test_print_player_card_with_and_without_properties(capsys):
    player = Player("Alice", balance=1600)
    ui.print_player_card(player)
    out = capsys.readouterr().out
    assert "Player  : Alice" in out
    assert "Properties: none" in out

    board = Board()
    prop = board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    player.in_jail = True
    player.jail_turns = 1
    player.get_out_of_jail_cards = 2

    ui.print_player_card(player)
    out = capsys.readouterr().out
    assert "IN JAIL" in out
    assert "Jail cards: 2" in out
    assert prop.name in out


def test_print_standings_orders_by_net_worth_and_marks_jail(capsys):
    a = Player("Alice", balance=900)
    b = Player("Bob", balance=1500)
    c = Player("Cara", balance=1200)
    c.in_jail = True

    ui.print_standings([a, b, c])
    out = capsys.readouterr().out

    bob_idx = out.index("Bob")
    cara_idx = out.index("Cara")
    alice_idx = out.index("Alice")
    assert bob_idx < cara_idx < alice_idx
    assert "[JAILED]" in out


def test_print_board_ownership_shows_owner_and_mortgage_marker(capsys):
    board = Board()
    owner = Player("Alice")
    prop = board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = True

    ui.print_board_ownership(board)
    out = capsys.readouterr().out

    assert "Property Register" in out
    assert prop.name in out
    assert "*Alice" in out
    assert "(* = mortgaged)" in out


def test_format_currency_handles_zero_and_large_amount():
    assert ui.format_currency(0) == "$0"
    assert ui.format_currency(1234567) == "$1,234,567"


def test_safe_int_input_valid_and_invalid(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "42")
    assert ui.safe_int_input("x", default=5) == 42

    monkeypatch.setattr("builtins.input", lambda _prompt: "not-a-number")
    assert ui.safe_int_input("x", default=5) == 5


def test_confirm_yes_and_no(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert ui.confirm("?") is True

    monkeypatch.setattr("builtins.input", lambda _prompt: "N")
    assert ui.confirm("?") is False
