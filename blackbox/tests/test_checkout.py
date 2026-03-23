"""
Test Checkout endpoint.
"""
import pytest
import requests
from conftest import api_url, get_admin_products, clear_cart, add_to_cart, remove_coupon


def _setup_cart(headers, admin_headers, target_total=1000):
    """Add items to cart approaching target_total. Returns approximate total."""
    clear_cart(headers)
    remove_coupon(headers)
    resp = get_admin_products(admin_headers)
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", [])

    total = 0
    for p in products:
        if not p.get("is_active", True):
            continue
        pid = p["product_id"]
        price = p.get("price", 0)
        stock = p.get("stock_quantity", 0)
        if stock > 0 and price > 0:
            qty = min(stock, max(1, int((target_total - total) / price) + 1))
            add_to_cart(headers, pid, qty)
            total += price * qty
            if total >= target_total:
                break
    return total


class TestCheckoutPaymentMethods:
    """POST /checkout — valid and invalid payment methods."""

    def test_checkout_cod(self, headers, admin_headers):
        total = _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "COD"},
        )
        if total <= 5000:
            assert resp.status_code == 200
        else:
            assert resp.status_code == 400

    def test_checkout_wallet(self, headers, admin_headers):
        requests.post(api_url("/wallet/add"), headers=headers, json={"amount": 100000})
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "WALLET"},
        )
        assert resp.status_code == 200

    def test_checkout_card(self, headers, admin_headers):
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "CARD"},
        )
        assert resp.status_code == 200

    @pytest.mark.parametrize("bad_method", ["CRYPTO", "UPI", "CASH", "", "cod", 123])
    def test_invalid_payment_methods(self, headers, admin_headers, bad_method):
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": bad_method},
        )
        assert resp.status_code == 400

    def test_missing_payment_method(self, headers, admin_headers):
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(api_url("/checkout"), headers=headers, json={})
        assert resp.status_code == 400


class TestCheckoutEmptyCart:
    def test_checkout_empty_cart(self, headers):
        clear_cart(headers)
        remove_coupon(headers)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "CARD"},
        )
        assert resp.status_code == 400


class TestCheckoutCODLimit:
    """COD not allowed if order total > 5000."""

    def test_cod_above_5000_rejected(self, headers, admin_headers):
        _setup_cart(headers, admin_headers, target_total=6000)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "COD"},
        )
        assert resp.status_code == 400


class TestCheckoutGST:
    """GST is 5% and applied only once."""

    def test_gst_calculation(self, headers, admin_headers):
        clear_cart(headers)
        remove_coupon(headers)

        resp_products = get_admin_products(admin_headers)
        products = resp_products.json()
        if isinstance(products, dict):
            products = products.get("products", [])

        # Add a single product
        pid = None
        price = 0
        for p in products:
            if p.get("is_active") and p.get("stock_quantity", 0) > 0:
                pid = p["product_id"]
                price = p["price"]
                break
        if pid is None:
            pytest.skip("No active products with stock")

        add_to_cart(headers, pid, 1)

        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "CARD"},
        )
        assert resp.status_code == 200
        data = resp.json()
        gst = data.get("gst_amount", 0)
        total = data.get("total_amount", 0)
        # GST should be 5% of price
        expected_gst = price * 0.05
        assert abs(gst - expected_gst) < 0.01, (
            f"GST {gst} != expected {expected_gst} (5% of {price})"
        )
        expected_total = price + expected_gst
        assert abs(total - expected_total) < 0.01, (
            f"Total {total} != expected {expected_total}"
        )


class TestCheckoutPaymentStatus:
    """COD/WALLET → PENDING, CARD → PAID."""

    def test_cod_payment_pending(self, headers, admin_headers):
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "COD"},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("payment_status") == "PENDING", (
                f"COD should be PENDING, got {data.get('payment_status')}"
            )

    def test_wallet_payment_pending(self, headers, admin_headers):
        requests.post(api_url("/wallet/add"), headers=headers, json={"amount": 100000})
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "WALLET"},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("payment_status") == "PENDING", (
                f"WALLET should be PENDING, got {data.get('payment_status')}"
            )

    def test_card_payment_paid(self, headers, admin_headers):
        _setup_cart(headers, admin_headers, target_total=500)
        resp = requests.post(
            api_url("/checkout"), headers=headers,
            json={"payment_method": "CARD"},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("payment_status") == "PAID", (
                f"CARD should be PAID, got {data.get('payment_status')}"
            )
