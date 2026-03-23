"""
Test common header validation across all endpoints.
"""
import pytest
import requests
from conftest import api_url, VALID_ROLL, VALID_USER_ID


# ─── Endpoints for testing ──────────────────────────────────────────
USER_SCOPED_ENDPOINTS = [
    ("GET", "/profile"),
    ("GET", "/addresses"),
    ("GET", "/cart"),
    ("GET", "/wallet"),
    ("GET", "/loyalty"),
    ("GET", "/orders"),
    ("GET", "/products"),
]

ADMIN_ENDPOINTS = [
    ("GET", "/admin/users"),
    ("GET", "/admin/carts"),
    ("GET", "/admin/orders"),
    ("GET", "/admin/products"),
    ("GET", "/admin/coupons"),
    ("GET", "/admin/tickets"),
    ("GET", "/admin/addresses"),
]


# ═══════════════════════════════════════════════════════════════════
# X-Roll-Number header tests
# ═══════════════════════════════════════════════════════════════════

class TestMissingRollNumber:
    """Missing X-Roll-Number must return 401 on every endpoint."""

    @pytest.mark.parametrize("method,path", USER_SCOPED_ENDPOINTS + ADMIN_ENDPOINTS)
    def test_missing_roll_number_returns_401(self, method, path):
        hdrs = {"X-User-ID": VALID_USER_ID, "Content-Type": "application/json"}
        resp = requests.request(method, api_url(path), headers=hdrs)
        assert resp.status_code == 401, (
            f"{method} {path}: expected 401, got {resp.status_code}"
        )


class TestInvalidRollNumber:
    """Non-integer X-Roll-Number must return 400."""

    @pytest.mark.parametrize("bad_roll", ["abc", "12.5", "!@#"])
    @pytest.mark.parametrize("method,path", [("GET", "/profile"), ("GET", "/admin/users")])
    def test_invalid_roll_number_returns_400(self, method, path, bad_roll):
        hdrs = {
            "X-Roll-Number": bad_roll,
            "X-User-ID": VALID_USER_ID,
            "Content-Type": "application/json",
        }
        resp = requests.request(method, api_url(path), headers=hdrs)
        assert resp.status_code == 400, (
            f"{method} {path} with roll='{bad_roll}': expected 400, got {resp.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════
# X-User-ID header tests (user-scoped endpoints only)
# ═══════════════════════════════════════════════════════════════════

class TestMissingUserId:
    """Missing X-User-ID on user-scoped endpoints must return 400."""

    @pytest.mark.parametrize("method,path", USER_SCOPED_ENDPOINTS)
    def test_missing_user_id_returns_400(self, method, path):
        hdrs = {"X-Roll-Number": VALID_ROLL, "Content-Type": "application/json"}
        resp = requests.request(method, api_url(path), headers=hdrs)
        assert resp.status_code == 400, (
            f"{method} {path}: expected 400 without X-User-ID, got {resp.status_code}"
        )


class TestInvalidUserId:
    """Invalid X-User-ID values on user-scoped endpoints must return 400."""

    @pytest.mark.parametrize("bad_uid", ["abc", "-1", "0", "12.5", "!@#"])
    def test_invalid_user_id_returns_400(self, bad_uid):
        hdrs = {
            "X-Roll-Number": VALID_ROLL,
            "X-User-ID": bad_uid,
            "Content-Type": "application/json",
        }
        resp = requests.get(api_url("/profile"), headers=hdrs)
        assert resp.status_code == 400, (
            f"profile with user_id='{bad_uid}': expected 400, got {resp.status_code}"
        )


class TestNonExistentUserId:
    """A non-existent but valid-format user ID should return 400."""

    def test_nonexistent_user_id(self):
        hdrs = {
            "X-Roll-Number": VALID_ROLL,
            "X-User-ID": "999999",
            "Content-Type": "application/json",
        }
        resp = requests.get(api_url("/profile"), headers=hdrs)
        assert resp.status_code in (400, 404), (
            f"profile with non-existent user: expected 400, got {resp.status_code}"
        )
