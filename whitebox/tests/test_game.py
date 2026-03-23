import pytest

from moneypoly.config import (
    AUCTION_MIN_INCREMENT,
    GO_SALARY,
    INCOME_TAX_AMOUNT,
    JAIL_FINE,
    JAIL_POSITION,
    LUXURY_TAX_AMOUNT,
    MAX_TURNS,
)
from moneypoly.game import Game
from moneypoly.player import Player


def _seq(values):
    it = iter(values)
    return lambda *args, **kwargs: next(it)


def test_current_player_and_advance_turn_cycle(game_two_players):
    game = game_two_players
    assert game.current_player().name == "Alice"

    game.advance_turn()
    assert game.current_player().name == "Bob"
    assert game.turn_number == 1

    game.advance_turn()
    assert game.current_player().name == "Alice"
    assert game.turn_number == 2


def test_play_turn_for_jailed_player_calls_jail_handler_and_advances(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    player.in_jail = True

    called = {"jail": False}

    def fake_handle(p):
        called["jail"] = True
        assert p is player

    monkeypatch.setattr(game, "_handle_jail_turn", fake_handle)

    game.play_turn()

    assert called["jail"] is True
    assert game.current_player().name == "Bob"


def test_play_turn_three_consecutive_doubles_sends_player_to_jail(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()

    def fake_roll():
        game.dice.die1 = 2
        game.dice.die2 = 2
        game.dice.doubles_streak = 3
        return 4

    monkeypatch.setattr(game.dice, "roll", fake_roll)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4 (DOUBLES)")

    game.play_turn()

    assert player.in_jail is True
    assert player.position == JAIL_POSITION
    assert game.current_player().name == "Bob"


def test_play_turn_with_doubles_gives_extra_turn(monkeypatch, game_two_players):
    game = game_two_players

    monkeypatch.setattr(game.dice, "roll", lambda: 6)
    monkeypatch.setattr(game.dice, "describe", lambda: "3 + 3 = 6 (DOUBLES)")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
    game.dice.doubles_streak = 1

    moved = {"called": False}
    monkeypatch.setattr(game, "_move_and_resolve", lambda p, s: moved.update(called=True))

    game.play_turn()

    assert moved["called"] is True
    assert game.current_player().name == "Alice"


def test_play_turn_non_doubles_advances_turn(monkeypatch, game_two_players):
    game = game_two_players
    monkeypatch.setattr(game.dice, "roll", lambda: 7)
    monkeypatch.setattr(game.dice, "describe", lambda: "3 + 4 = 7")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    game.dice.doubles_streak = 0
    monkeypatch.setattr(game, "_move_and_resolve", lambda p, s: None)

    game.play_turn()
    assert game.current_player().name == "Bob"


@pytest.mark.parametrize(
    ("tile", "expected_delta", "expected_bank_delta", "jail_expected"),
    [
        ("income_tax", -INCOME_TAX_AMOUNT, INCOME_TAX_AMOUNT, False),
        ("luxury_tax", -LUXURY_TAX_AMOUNT, LUXURY_TAX_AMOUNT, False),
        ("go_to_jail", 0, 0, True),
        ("free_parking", 0, 0, False),
        ("blank", 0, 0, False),
    ],
)
def test_move_and_resolve_core_tile_branches(
    monkeypatch,
    game_two_players,
    tile,
    expected_delta,
    expected_bank_delta,
    jail_expected,
):
    game = game_two_players
    player = game.current_player()

    monkeypatch.setattr(player, "move", lambda _steps: None)
    monkeypatch.setattr(game.board, "get_tile_type", lambda _pos: tile)
    start_balance = player.balance
    start_bank = game.bank.get_balance()

    game._move_and_resolve(player, 4)

    assert player.balance == start_balance + expected_delta
    assert game.bank.get_balance() == start_bank + expected_bank_delta
    assert player.in_jail is jail_expected


def test_move_and_resolve_draws_card_for_chance_and_community(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()

    applied = []
    monkeypatch.setattr(player, "move", lambda _steps: None)
    monkeypatch.setattr(game, "_apply_card", lambda p, card: applied.append((p, card)))

    monkeypatch.setattr(game.board, "get_tile_type", lambda _pos: "chance")
    monkeypatch.setattr(game.decks["chance"], "draw", lambda: {"action": "collect", "value": 10, "description": "x"})
    game._move_and_resolve(player, 1)

    monkeypatch.setattr(game.board, "get_tile_type", lambda _pos: "community_chest")
    monkeypatch.setattr(game.decks["community_chest"], "draw", lambda: {"action": "pay", "value": 10, "description": "y"})
    game._move_and_resolve(player, 1)

    assert len(applied) == 2
    assert applied[0][0] is player
    assert applied[1][0] is player


@pytest.mark.parametrize("tile", ["railroad", "property"])
def test_move_and_resolve_property_like_tiles_call_handler_when_property_exists(
    monkeypatch, game_two_players, tile
):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)

    monkeypatch.setattr(player, "move", lambda _steps: None)
    monkeypatch.setattr(game.board, "get_tile_type", lambda _pos: tile)
    monkeypatch.setattr(game.board, "get_property_at", lambda _pos: prop)

    called = {"count": 0}
    monkeypatch.setattr(game, "_handle_property_tile", lambda p, pr: called.update(count=called["count"] + 1))

    game._move_and_resolve(player, 1)
    assert called["count"] == 1


def test_handle_property_tile_unowned_buy(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)
    prop.owner = None

    called = {"buy": False}
    monkeypatch.setattr("builtins.input", lambda _prompt: "b")
    monkeypatch.setattr(game, "buy_property", lambda p, pr: called.update(buy=True))

    game._handle_property_tile(player, prop)
    assert called["buy"] is True


def test_handle_property_tile_unowned_auction(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)
    prop.owner = None

    called = {"auction": False}
    monkeypatch.setattr("builtins.input", lambda _prompt: "a")
    monkeypatch.setattr(game, "auction_property", lambda pr: called.update(auction=True))

    game._handle_property_tile(player, prop)
    assert called["auction"] is True


def test_handle_property_tile_unowned_skip(monkeypatch, game_two_players, capsys):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)
    prop.owner = None

    monkeypatch.setattr("builtins.input", lambda _prompt: "s")

    game._handle_property_tile(player, prop)
    assert "passes" in capsys.readouterr().out


def test_handle_property_tile_owned_by_self_and_other(monkeypatch, game_two_players, capsys):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = alice
    game._handle_property_tile(alice, prop)
    assert "No rent due" in capsys.readouterr().out

    called = {"rent": False}
    prop.owner = bob
    monkeypatch.setattr(game, "pay_rent", lambda p, pr: called.update(rent=True))
    game._handle_property_tile(alice, prop)
    assert called["rent"] is True


def test_buy_property_success_and_insufficient_funds(game_two_players):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)

    prop.price = 200
    player.balance = 500
    start_bank = game.bank.get_balance()

    assert game.buy_property(player, prop) is True
    assert prop.owner is player
    assert prop in player.properties
    assert player.balance == 300
    assert game.bank.get_balance() == start_bank + 200

    poor = Player("Poor", balance=100)
    expensive = game.board.get_property_at(3)
    expensive.price = 300
    assert game.buy_property(poor, expensive) is False


def test_buy_property_should_allow_exact_balance(game_two_players):
    game = game_two_players
    player = game.current_player()
    prop = game.board.get_property_at(1)

    player.balance = 300
    prop.price = 300

    assert game.buy_property(player, prop) is True


def test_pay_rent_mortgaged_or_unowned_no_payment(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    # mortgaged branch
    prop.owner = bob
    prop.is_mortgaged = True
    start = alice.balance
    game.pay_rent(alice, prop)
    assert alice.balance == start

    # unowned branch
    prop.is_mortgaged = False
    prop.owner = None
    game.pay_rent(alice, prop)
    assert alice.balance == start


def test_pay_rent_deducts_from_player(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)
    prop.owner = bob
    prop.base_rent = 40

    alice_start = alice.balance
    game.pay_rent(alice, prop)

    assert alice.balance == alice_start - prop.get_rent()


def test_pay_rent_should_credit_owner(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)
    prop.owner = bob
    prop.base_rent = 40

    owner_start = bob.balance
    game.pay_rent(alice, prop)

    assert bob.balance == owner_start + prop.get_rent()


def test_mortgage_property_branches(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = bob
    assert game.mortgage_property(alice, prop) is False

    prop.owner = alice
    alice.add_property(prop)
    assert game.mortgage_property(alice, prop) is True
    assert prop.is_mortgaged is True

    # already mortgaged
    assert game.mortgage_property(alice, prop) is False


def test_unmortgage_property_branches(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = bob
    assert game.unmortgage_property(alice, prop) is False

    prop.owner = alice
    alice.add_property(prop)

    # not mortgaged
    assert game.unmortgage_property(alice, prop) is False

    prop.is_mortgaged = True
    alice.balance = 0
    assert game.unmortgage_property(alice, prop) is False

    prop.is_mortgaged = True
    alice.balance = 1000
    assert game.unmortgage_property(alice, prop) is True
    assert prop.is_mortgaged is False


def test_trade_failure_paths(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = bob
    assert game.trade(alice, bob, prop, 100) is False

    prop.owner = alice
    alice.add_property(prop)
    bob.balance = 50
    assert game.trade(alice, bob, prop, 100) is False


def test_trade_success_transfers_property(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = alice
    alice.add_property(prop)
    bob.balance = 500

    assert game.trade(alice, bob, prop, 200) is True
    assert prop.owner is bob
    assert prop not in alice.properties
    assert prop in bob.properties
    assert bob.balance == 300


def test_trade_should_credit_seller(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    prop.owner = alice
    alice.add_property(prop)
    alice_start = alice.balance

    assert game.trade(alice, bob, prop, 200) is True
    assert alice.balance == alice_start + 200


def test_trade_with_negative_cash_is_rejected_by_player_guard(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)
    prop.owner = alice
    alice.add_property(prop)

    with pytest.raises(ValueError):
        game.trade(alice, bob, prop, -10)


def test_auction_property_no_bids(monkeypatch, game_two_players):
    game = game_two_players
    prop = game.board.get_property_at(1)

    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([0, 0]))
    game.auction_property(prop)

    assert prop.owner is None


def test_auction_property_with_invalid_and_valid_bids(monkeypatch, game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)

    # Alice low bid (< min raise), Bob over-balance, then second run with winner.
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([
        AUCTION_MIN_INCREMENT - 1,
        bob.balance + 1,
    ]))
    game.auction_property(prop)
    assert prop.owner is None

    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([100, 50]))
    start_bank = game.bank.get_balance()
    game.auction_property(prop)

    assert prop.owner is alice
    assert prop in alice.properties
    assert alice.balance == 1400
    assert game.bank.get_balance() == start_bank + 100


def test_handle_jail_turn_uses_jail_free_card(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    player.in_jail = True
    player.get_out_of_jail_cards = 1

    monkeypatch.setattr("moneypoly.game.ui.confirm", _seq([True]))
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")

    moved = {"called": False}
    monkeypatch.setattr(game, "_move_and_resolve", lambda p, r: moved.update(called=True))

    game._handle_jail_turn(player)

    assert player.get_out_of_jail_cards == 0
    assert player.in_jail is False
    assert player.jail_turns == 0
    assert moved["called"] is True


def test_handle_jail_turn_pay_fine_should_deduct_player_balance(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    player.in_jail = True

    monkeypatch.setattr("moneypoly.game.ui.confirm", _seq([True]))
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(game, "_move_and_resolve", lambda p, r: None)

    start_balance = player.balance
    game._handle_jail_turn(player)

    assert player.balance == start_balance - JAIL_FINE


def test_handle_jail_turn_no_action_increments_and_mandatory_release(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    player.in_jail = True
    player.jail_turns = 1

    monkeypatch.setattr("moneypoly.game.ui.confirm", _seq([False]))
    game._handle_jail_turn(player)

    assert player.in_jail is True
    assert player.jail_turns == 2

    # Third missed turn triggers mandatory release + fine deduction.
    monkeypatch.setattr("moneypoly.game.ui.confirm", _seq([False]))
    monkeypatch.setattr(game.dice, "roll", lambda: 6)
    monkeypatch.setattr(game.dice, "describe", lambda: "3 + 3 = 6")
    monkeypatch.setattr(game, "_move_and_resolve", lambda p, r: None)

    before = player.balance
    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.jail_turns == 0
    assert player.balance == before - JAIL_FINE


def test_apply_card_all_action_branches(monkeypatch, game_two_players):
    game = game_two_players
    alice, bob = game.players

    # None branch
    before = alice.balance
    game._apply_card(alice, None)
    assert alice.balance == before

    # collect
    game._apply_card(alice, {"description": "c", "action": "collect", "value": 50})
    assert alice.balance == before + 50

    # pay
    game._apply_card(alice, {"description": "p", "action": "pay", "value": 30})
    assert alice.balance == before + 20

    # jail
    game._apply_card(alice, {"description": "j", "action": "jail", "value": 0})
    assert alice.in_jail is True

    # jail_free
    game._apply_card(alice, {"description": "jf", "action": "jail_free", "value": 0})
    assert alice.get_out_of_jail_cards == 1

    # move_to dispatch
    moved = {"called": False}
    monkeypatch.setattr(game, "_card_action_move_to", lambda p, v: moved.update(called=True))
    game._apply_card(alice, {"description": "m", "action": "move_to", "value": 5})
    assert moved["called"] is True

    # birthday / collect_from_all dispatch
    collected = {"count": 0}
    monkeypatch.setattr(
        game,
        "_card_action_collect_from_all",
        lambda p, v: collected.update(count=collected["count"] + 1),
    )
    game._apply_card(alice, {"description": "b", "action": "birthday", "value": 10})
    game._apply_card(alice, {"description": "a", "action": "collect_from_all", "value": 10})
    assert collected["count"] == 2


def test_card_action_move_to_pass_go_and_property_handler(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()
    player.position = 39
    start = player.balance

    prop = game.board.get_property_at(1)
    monkeypatch.setattr(game.board, "get_tile_type", lambda pos: "property")
    monkeypatch.setattr(game.board, "get_property_at", lambda pos: prop)

    called = {"handled": False}
    monkeypatch.setattr(game, "_handle_property_tile", lambda p, pr: called.update(handled=True))

    game._card_action_move_to(player, 1)

    assert player.position == 1
    assert player.balance == start + GO_SALARY
    assert called["handled"] is True


def test_card_action_collect_from_all_only_from_players_with_enough_balance(game_two_players):
    game = game_two_players
    alice, bob = game.players
    cara = Player("Cara", balance=5)
    game.players.append(cara)

    start_alice = alice.balance
    start_bob = bob.balance
    start_cara = cara.balance

    game._card_action_collect_from_all(alice, 10)

    assert alice.balance == start_alice + 10  # only Bob can pay
    assert bob.balance == start_bob - 10
    assert cara.balance == start_cara


def test_check_bankruptcy_non_bankrupt_and_bankrupt_paths(game_two_players):
    game = game_two_players
    alice, bob = game.players
    prop = game.board.get_property_at(1)
    prop.owner = alice
    prop.is_mortgaged = True
    alice.add_property(prop)

    # non-bankrupt path
    alice.balance = 1
    game._check_bankruptcy(alice)
    assert alice in game.players

    # bankrupt path
    alice.balance = 0
    game.current_index = 1
    game._check_bankruptcy(alice)

    assert alice not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False
    assert game.current_index == 0


def test_find_winner_no_players_returns_none():
    game = Game(["Alice", "Bob"])
    game.players = []
    assert game.find_winner() is None


def test_find_winner_should_return_highest_net_worth_player(game_two_players):
    game = game_two_players
    game.players[0].balance = 100
    game.players[1].balance = 200
    assert game.find_winner() is game.players[1]


def test_run_branches_winner_and_no_players(monkeypatch, capsys):
    # Winner branch
    game = Game(["Alice", "Bob"])

    monkeypatch.setattr("moneypoly.game.MAX_TURNS", 1)
    monkeypatch.setattr(game, "play_turn", lambda: setattr(game, "turn_number", 1))
    monkeypatch.setattr("moneypoly.game.ui.print_banner", lambda _title: None)
    monkeypatch.setattr("moneypoly.game.ui.print_standings", lambda _players: None)

    game.run()
    out = capsys.readouterr().out
    assert "wins with a net worth" in out

    # No-players branch
    empty_game = Game(["Solo"])
    empty_game.players = []
    monkeypatch.setattr(empty_game, "play_turn", lambda: None)
    empty_game.run()
    out = capsys.readouterr().out
    assert "no players remaining" in out


def test_interactive_menu_routes_all_choices(monkeypatch, game_two_players):
    game = game_two_players
    player = game.current_player()

    called = {
        "standings": 0,
        "ownership": 0,
        "mortgage": 0,
        "unmortgage": 0,
        "trade": 0,
        "loan": 0,
    }

    monkeypatch.setattr(
        "moneypoly.game.ui.safe_int_input",
        _seq([1, 2, 3, 4, 5, 6, 250, 0]),
    )
    monkeypatch.setattr("moneypoly.game.ui.print_standings", lambda _p: called.update(standings=called["standings"] + 1))
    monkeypatch.setattr("moneypoly.game.ui.print_board_ownership", lambda _b: called.update(ownership=called["ownership"] + 1))
    monkeypatch.setattr(game, "_menu_mortgage", lambda _p: called.update(mortgage=called["mortgage"] + 1))
    monkeypatch.setattr(game, "_menu_unmortgage", lambda _p: called.update(unmortgage=called["unmortgage"] + 1))
    monkeypatch.setattr(game, "_menu_trade", lambda _p: called.update(trade=called["trade"] + 1))
    monkeypatch.setattr(game.bank, "give_loan", lambda p, amount: called.update(loan=amount))

    game.interactive_menu(player)

    assert called["standings"] == 1
    assert called["ownership"] == 1
    assert called["mortgage"] == 1
    assert called["unmortgage"] == 1
    assert called["trade"] == 1
    assert called["loan"] == 250


def test_menu_mortgage_branches(monkeypatch, game_two_players, capsys):
    game = game_two_players
    player = game.current_player()

    # no mortgageable branch
    game._menu_mortgage(player)
    assert "No properties available to mortgage" in capsys.readouterr().out

    # selection branch + invalid index branch
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)

    called = {"mortgage": 0}
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([2, 1]))
    monkeypatch.setattr(game, "mortgage_property", lambda p, pr: called.update(mortgage=called["mortgage"] + 1))

    game._menu_mortgage(player)  # invalid index -> no call
    game._menu_mortgage(player)  # valid index -> call

    assert called["mortgage"] == 1


def test_menu_unmortgage_branches(monkeypatch, game_two_players, capsys):
    game = game_two_players
    player = game.current_player()

    game._menu_unmortgage(player)
    assert "No mortgaged properties to redeem" in capsys.readouterr().out

    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)

    called = {"unmortgage": 0}
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([2, 1]))
    monkeypatch.setattr(game, "unmortgage_property", lambda p, pr: called.update(unmortgage=called["unmortgage"] + 1))

    game._menu_unmortgage(player)  # invalid index
    game._menu_unmortgage(player)  # valid index

    assert called["unmortgage"] == 1


def test_menu_trade_branches(monkeypatch, game_two_players, capsys):
    game = game_two_players
    alice, bob = game.players

    # no others branch
    solo = Game(["Solo"])
    solo._menu_trade(solo.players[0])
    assert "No other players to trade with" in capsys.readouterr().out

    # invalid partner selection branch
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([99]))
    game._menu_trade(alice)

    # no properties branch
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([1]))
    game._menu_trade(alice)
    assert "has no properties to trade" in capsys.readouterr().out

    # invalid property selection then valid trade
    prop = game.board.get_property_at(1)
    prop.owner = alice
    alice.add_property(prop)

    called = {"trade": 0}
    monkeypatch.setattr(game, "trade", lambda s, b, p, c: called.update(trade=called["trade"] + 1))
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", _seq([1, 99, 1, 1, 250]))

    game._menu_trade(alice)  # invalid property index
    game._menu_trade(alice)  # valid path

    assert called["trade"] == 1
