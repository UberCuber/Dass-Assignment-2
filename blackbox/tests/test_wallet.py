"""
Test Wallet endpoints.
"""
import pytest
import requests
from conftest import api_url


class TestGetWallet:
    def test_get_wallet_balance(self, headers):
        resp = requests.get(api_url("/wallet"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "wallet_balance" in data


class TestWalletAdd:
    """POST /wallet/add — amount > 0 and <= 100000."""

    def test_add_valid_amount(self, headers):
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 100},
        )
        assert resp.status_code == 200

    def test_add_minimum_amount(self, headers):
        """Boundary: amount = 1 (just above 0)."""
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 1},
        )
        assert resp.status_code == 200

    def test_add_maximum_amount(self, headers):
        """Boundary: amount = 100000."""
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 100000},
        )
        assert resp.status_code == 200

    def test_add_zero_rejected(self, headers):
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 0},
        )
        assert resp.status_code == 400

    def test_add_negative_rejected(self, headers):
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": -100},
        )
        assert resp.status_code == 400

    def test_add_above_max_rejected(self, headers):
        """Boundary: amount = 100001."""
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 100001},
        )
        assert resp.status_code == 400

    def test_add_non_numeric_rejected(self, headers):
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": "abc"},
        )
        assert resp.status_code == 400

    def test_add_missing_amount(self, headers):
        resp = requests.post(
            api_url("/wallet/add"), headers=headers,
            json={},
        )
        assert resp.status_code == 400


class TestWalletPay:
    """POST /wallet/pay."""

    def test_pay_valid(self, headers):
        # First add money
        requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 500},
        )
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={"amount": 100},
        )
        assert resp.status_code == 200

    def test_pay_zero_rejected(self, headers):
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={"amount": 0},
        )
        assert resp.status_code == 400

    def test_pay_negative_rejected(self, headers):
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={"amount": -50},
        )
        assert resp.status_code == 400

    def test_pay_insufficient_balance(self, headers):
        resp_bal = requests.get(api_url("/wallet"), headers=headers)
        data = resp_bal.json()
        balance = data.get("wallet_balance", 0)
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={"amount": balance + 999999},
        )
        assert resp.status_code == 400

    def test_pay_exact_deduction(self, headers):
        """Balance should decrease by the exact amount paid."""
        # Add known amount
        requests.post(
            api_url("/wallet/add"), headers=headers,
            json={"amount": 1000},
        )
        before = requests.get(api_url("/wallet"), headers=headers).json()
        before_bal = before.get("wallet_balance", 0)

        pay_amount = 250
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={"amount": pay_amount},
        )
        assert resp.status_code == 200

        after = requests.get(api_url("/wallet"), headers=headers).json()
        after_bal = after.get("wallet_balance", 0)

        expected = round(before_bal - pay_amount, 2)
        actual = round(after_bal, 2)
        assert abs(expected - actual) < 1.0, (
            f"Expected balance {expected}, got {actual} — wallet deducted extra"
        )

    def test_pay_missing_amount(self, headers):
        resp = requests.post(
            api_url("/wallet/pay"), headers=headers,
            json={},
        )
        assert resp.status_code == 400
