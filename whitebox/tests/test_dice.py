import pytest

from moneypoly.dice import Dice


def _sequence_randint(values):
    vals = iter(values)

    def inner(_low, _high):
        return next(vals)

    return inner


def test_reset_sets_values_and_streak_to_zero():
    dice = Dice()
    dice.die1 = 4
    dice.die2 = 2
    dice.doubles_streak = 3

    dice.reset()

    assert dice.die1 == 0
    assert dice.die2 == 0
    assert dice.doubles_streak == 0


def test_roll_updates_total_and_doubles_streak(monkeypatch):
    dice = Dice()

    monkeypatch.setattr("moneypoly.dice.random.randint", _sequence_randint([3, 3, 2, 5]))

    total_1 = dice.roll()
    assert total_1 == 6
    assert dice.is_doubles() is True
    assert dice.doubles_streak == 1

    total_2 = dice.roll()
    assert total_2 == 7
    assert dice.is_doubles() is False
    assert dice.doubles_streak == 0


def test_total_and_describe_branches():
    dice = Dice()
    dice.die1 = 2
    dice.die2 = 2
    assert dice.total() == 4
    assert "DOUBLES" in dice.describe()

    dice.die2 = 3
    assert dice.total() == 5
    assert "DOUBLES" not in dice.describe()


def test_roll_should_use_full_six_sided_range(monkeypatch):
    calls = []

    def fake_randint(low, high):
        calls.append((low, high))
        return 1

    monkeypatch.setattr("moneypoly.dice.random.randint", fake_randint)
    dice = Dice()
    dice.roll()

    assert calls == [(1, 6), (1, 6)]


def test_repr_includes_faces_and_streak():
    dice = Dice()
    dice.die1 = 5
    dice.die2 = 1
    dice.doubles_streak = 2

    text = repr(dice)
    assert "die1=5" in text
    assert "die2=1" in text
    assert "streak=2" in text
