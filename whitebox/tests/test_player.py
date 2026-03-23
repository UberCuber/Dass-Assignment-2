import pytest

from moneypoly.config import BOARD_SIZE, GO_SALARY, STARTING_BALANCE, JAIL_POSITION
from moneypoly.player import Player


class DummyProperty:
    pass


def test_player_init_defaults():
    p = Player("Alice")
    assert p.name == "Alice"
    assert p.balance == STARTING_BALANCE
    assert p.position == 0
    assert p.properties == []
    assert p.in_jail is False
    assert p.jail_turns == 0
    assert p.get_out_of_jail_cards == 0


def test_add_money_and_negative_guard():
    p = Player("Alice")
    p.add_money(100)
    assert p.balance == STARTING_BALANCE + 100

    with pytest.raises(ValueError):
        p.add_money(-1)


def test_deduct_money_and_negative_guard():
    p = Player("Alice")
    p.deduct_money(300)
    assert p.balance == STARTING_BALANCE - 300

    with pytest.raises(ValueError):
        p.deduct_money(-10)


def test_is_bankrupt_thresholds():
    p = Player("Alice", balance=1)
    assert p.is_bankrupt() is False

    p.balance = 0
    assert p.is_bankrupt() is True

    p.balance = -5
    assert p.is_bankrupt() is True


def test_move_landing_on_go_collects_salary(capsys):
    p = Player("Alice")
    p.position = BOARD_SIZE - 1

    pos = p.move(1)

    assert pos == 0
    assert p.balance == STARTING_BALANCE + GO_SALARY
    assert "landed on Go" in capsys.readouterr().out


def test_move_passing_go_should_collect_salary():
    p = Player("Alice")
    p.position = BOARD_SIZE - 1

    pos = p.move(2)

    assert pos == 1
    assert p.balance == STARTING_BALANCE + GO_SALARY


def test_move_wraps_and_handles_large_steps_without_salary_when_not_go():
    p = Player("Alice")
    p.position = 5
    pos = p.move(BOARD_SIZE * 3 + 7)
    assert pos == 12
    assert p.balance == STARTING_BALANCE


def test_go_to_jail_sets_expected_state():
    p = Player("Alice")
    p.position = 25
    p.jail_turns = 2

    p.go_to_jail()

    assert p.position == JAIL_POSITION
    assert p.in_jail is True
    assert p.jail_turns == 0


def test_add_and_remove_property_no_duplicates():
    p = Player("Alice")
    prop = DummyProperty()

    p.add_property(prop)
    p.add_property(prop)
    assert p.count_properties() == 1

    p.remove_property(prop)
    assert p.count_properties() == 0

    # Removing missing property should be a no-op
    p.remove_property(prop)
    assert p.count_properties() == 0


def test_status_line_with_and_without_jail_tag():
    p = Player("Alice")
    normal = p.status_line()
    assert "[JAILED]" not in normal

    p.in_jail = True
    jailed = p.status_line()
    assert "[JAILED]" in jailed


def test_net_worth_matches_balance():
    p = Player("Alice", balance=1234)
    assert p.net_worth() == 1234


def test_repr_contains_key_fields():
    p = Player("Alice", balance=1200)
    p.position = 4
    text = repr(p)
    assert "Alice" in text
    assert "balance=1200" in text
    assert "pos=4" in text
