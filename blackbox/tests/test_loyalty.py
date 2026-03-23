"""
Test Loyalty Points endpoints.
"""
import pytest
import requests
from conftest import api_url


class TestGetLoyalty:
    def test_get_loyalty_points(self, headers):
        resp = requests.get(api_url("/loyalty"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "loyalty_points" in data


class TestRedeemLoyalty:
    """POST /loyalty/redeem."""

    def test_redeem_valid(self, headers):
        resp = requests.get(api_url("/loyalty"), headers=headers)
        points = resp.json().get("loyalty_points", 0)
        if points < 1:
            pytest.skip("Not enough loyalty points")
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={"points": 1})
        assert resp.status_code == 200

    def test_redeem_more_than_available(self, headers):
        resp = requests.get(api_url("/loyalty"), headers=headers)
        points = resp.json().get("loyalty_points", 0)
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={"points": points + 999999})
        assert resp.status_code == 400

    def test_redeem_zero_rejected(self, headers):
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={"points": 0})
        assert resp.status_code == 400

    def test_redeem_negative_rejected(self, headers):
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={"points": -5})
        assert resp.status_code == 400

    def test_redeem_missing_points(self, headers):
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={})
        assert resp.status_code == 400

    def test_redeem_non_integer(self, headers):
        resp = requests.post(api_url("/loyalty/redeem"), headers=headers, json={"points": "abc"})
        assert resp.status_code == 400
