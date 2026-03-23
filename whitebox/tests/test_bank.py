import pytest

from moneypoly.bank import Bank
from moneypoly.config import BANK_STARTING_FUNDS
from moneypoly.player import Player


def test_bank_initial_state():
    bank = Bank()
    assert bank.get_balance() == BANK_STARTING_FUNDS
    assert bank.loan_count() == 0
    assert bank.total_loans_issued() == 0


def test_collect_positive_amount_updates_funds_and_total_collected():
    bank = Bank()
    bank.collect(250)
    assert bank.get_balance() == BANK_STARTING_FUNDS + 250
    assert bank._total_collected == 250


def test_collect_negative_amount_should_be_ignored():
    bank = Bank()
    bank.collect(-100)
    assert bank.get_balance() == BANK_STARTING_FUNDS
    assert bank._total_collected == 0


@pytest.mark.parametrize("amount", [0, -10])
def test_pay_out_non_positive_returns_zero_and_keeps_balance(amount):
    bank = Bank()
    paid = bank.pay_out(amount)
    assert paid == 0
    assert bank.get_balance() == BANK_STARTING_FUNDS


def test_pay_out_valid_amount_reduces_balance():
    bank = Bank()
    paid = bank.pay_out(500)
    assert paid == 500
    assert bank.get_balance() == BANK_STARTING_FUNDS - 500


def test_pay_out_raises_for_insufficient_funds():
    bank = Bank()
    with pytest.raises(ValueError):
        bank.pay_out(BANK_STARTING_FUNDS + 1)


@pytest.mark.parametrize("amount", [0, -1])
def test_give_loan_non_positive_does_nothing(amount):
    bank = Bank()
    player = Player("Alice")
    before_balance = player.balance
    bank.give_loan(player, amount)
    assert player.balance == before_balance
    assert bank.loan_count() == 0


def test_give_loan_records_loan_and_credits_player(capsys):
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 200)

    assert player.balance == 1700
    assert bank.loan_count() == 1
    assert bank.total_loans_issued() == 200

    captured = capsys.readouterr()
    assert "emergency loan" in captured.out.lower()


def test_give_loan_should_reduce_bank_funds():
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 200)
    assert bank.get_balance() == BANK_STARTING_FUNDS - 200


def test_summary_and_repr(capsys):
    bank = Bank()
    bank.collect(100)
    bank.summary()

    out = capsys.readouterr().out
    assert "Bank reserves" in out
    assert "Total collected" in out
    assert "Loans issued" in out
    assert repr(bank).startswith("Bank(funds=")
