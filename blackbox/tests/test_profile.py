"""
Test Profile endpoints: GET /profile, PUT /profile.
"""
import pytest
import requests
from conftest import api_url


class TestGetProfile:
    """GET /profile."""

    def test_get_profile_success(self, headers):
        resp = requests.get(api_url("/profile"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestUpdateProfile:
    """PUT /profile — name and phone validation."""

    # ── Valid updates ───────────────────────────────────────────────
    def test_update_valid(self, headers):
        payload = {"name": "Test User", "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 200

    # ── Name boundary: min 2 chars ─────────────────────────────────
    def test_name_exactly_2_chars(self, headers):
        payload = {"name": "AB", "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 200

    def test_name_1_char_rejected(self, headers):
        payload = {"name": "A", "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    # ── Name boundary: max 50 chars ────────────────────────────────
    def test_name_exactly_50_chars(self, headers):
        payload = {"name": "A" * 50, "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 200

    def test_name_51_chars_rejected(self, headers):
        payload = {"name": "A" * 51, "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    # ── Phone: exactly 10 digits ───────────────────────────────────
    def test_phone_9_digits_rejected(self, headers):
        payload = {"name": "TestUser", "phone": "123456789"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_phone_10_digits_valid(self, headers):
        payload = {"name": "TestUser", "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 200

    def test_phone_11_digits_rejected(self, headers):
        payload = {"name": "TestUser", "phone": "12345678901"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_phone_non_numeric_rejected(self, headers):
        payload = {"name": "TestUser", "phone": "abcdefghij"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    # ── Missing fields ─────────────────────────────────────────────
    def test_missing_name(self, headers):
        payload = {"phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_missing_phone(self, headers):
        payload = {"name": "TestUser"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_empty_body(self, headers):
        resp = requests.put(api_url("/profile"), headers=headers, json={})
        assert resp.status_code == 400

    # ── Wrong data types ───────────────────────────────────────────
    def test_name_as_integer(self, headers):
        payload = {"name": 12345, "phone": "1234567890"}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_phone_as_integer(self, headers):
        payload = {"name": "TestUser", "phone": 1234567890}
        resp = requests.put(api_url("/profile"), headers=headers, json=payload)
        assert resp.status_code == 400
