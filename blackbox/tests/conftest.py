"""
Shared fixtures and helpers for QuickCart black-box tests.
"""
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8080/api/v1"

VALID_ROLL = "2024101114"
VALID_USER_ID = "1"


def api_url(path: str) -> str:
    """Build full API URL from a relative path."""
    return f"{BASE_URL}{path}"


@pytest.fixture()
def headers():
    """Return standard valid headers for user-scoped requests."""
    return {
        "X-Roll-Number": VALID_ROLL,
        "X-User-ID": VALID_USER_ID,
        "Content-Type": "application/json",
    }


@pytest.fixture()
def admin_headers():
    """Return headers for admin endpoints (no X-User-ID needed)."""
    return {
        "X-Roll-Number": VALID_ROLL,
        "X-User-ID": VALID_USER_ID,
        "Content-Type": "application/json",
    }


# ─── Helper functions ──────────────────────────────────────────────

def get_admin_users(admin_headers):
    return requests.get(api_url("/admin/users"), headers=admin_headers)


def get_admin_products(admin_headers):
    return requests.get(api_url("/admin/products"), headers=admin_headers)


def get_admin_coupons(admin_headers):
    return requests.get(api_url("/admin/coupons"), headers=admin_headers)


def get_admin_carts(admin_headers):
    return requests.get(api_url("/admin/carts"), headers=admin_headers)


def get_admin_orders(admin_headers):
    return requests.get(api_url("/admin/orders"), headers=admin_headers)


def clear_cart(headers):
    """Clear the user's cart."""
    return requests.delete(api_url("/cart/clear"), headers=headers)


def add_to_cart(headers, product_id, quantity):
    """Add a product to the user's cart."""
    return requests.post(
        api_url("/cart/add"),
        headers=headers,
        json={"product_id": product_id, "quantity": quantity},
    )


def remove_coupon(headers):
    """Remove any applied coupon."""
    return requests.post(api_url("/coupon/remove"), headers=headers)


def is_coupon_expired(coupon):
    """Check if a coupon is expired by comparing expiry_date to now."""
    expiry_str = coupon.get("expiry_date", "")
    if not expiry_str:
        return False
    try:
        expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
        return expiry < datetime.now(timezone.utc)
    except Exception:
        return False
