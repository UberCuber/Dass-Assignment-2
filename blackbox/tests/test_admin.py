"""
Test Admin / Data-inspection endpoints.
"""
import pytest
import requests
from conftest import api_url


class TestAdminUsers:
    """GET /admin/users and /admin/users/{id}."""

    def test_get_all_users(self, admin_headers):
        resp = requests.get(api_url("/admin/users"), headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_get_user_by_valid_id(self, admin_headers):
        resp = requests.get(api_url("/admin/users/1"), headers=admin_headers)
        assert resp.status_code == 200
        user = resp.json()
        # Should contain wallet_balance and loyalty_points
        assert "wallet_balance" in str(user).lower() or "balance" in str(user).lower()

    def test_get_user_by_nonexistent_id(self, admin_headers):
        resp = requests.get(api_url("/admin/users/999999"), headers=admin_headers)
        assert resp.status_code == 404

    def test_get_user_by_invalid_id(self, admin_headers):
        resp = requests.get(api_url("/admin/users/abc"), headers=admin_headers)
        assert resp.status_code in (400, 404)


class TestAdminCollections:
    """GET all collections for admin."""

    @pytest.mark.parametrize("endpoint", [
        "/admin/carts",
        "/admin/orders",
        "/admin/products",
        "/admin/coupons",
        "/admin/tickets",
        "/admin/addresses",
    ])
    def test_get_admin_collection(self, admin_headers, endpoint):
        resp = requests.get(api_url(endpoint), headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))
