"""
Test Cart endpoints.
"""
import pytest
import requests
from conftest import api_url, get_admin_products, clear_cart


def _get_first_active_product(admin_headers):
    """Return (product_id, stock_quantity, price) for the first active product."""
    resp = get_admin_products(admin_headers)
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", [])
    for p in products:
        if p.get("is_active", True):
            pid = p.get("product_id") or p.get("id")
            stock = p.get("stock_quantity", 0)
            price = p.get("price", 0)
            return pid, stock, price
    return None, None, None


class TestGetCart:
    def test_get_cart(self, headers):
        resp = requests.get(api_url("/cart"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


class TestAddToCart:
    """POST /cart/add."""

    def test_add_valid_item(self, headers, admin_headers):
        clear_cart(headers)
        pid, stock, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No active products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        assert resp.status_code == 200

    def test_add_quantity_zero_rejected(self, headers, admin_headers):
        """Spec: quantity must be at least 1. Sending 0 must be rejected with 400."""
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 0},
        )
        assert resp.status_code == 400, (
            f"BUG: Adding quantity=0 should return 400, got {resp.status_code}"
        )

    def test_add_negative_quantity_rejected(self, headers, admin_headers):
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": -1},
        )
        assert resp.status_code == 400

    def test_add_nonexistent_product(self, headers):
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": 999999, "quantity": 1},
        )
        assert resp.status_code == 404

    def test_add_exceeds_stock(self, headers, admin_headers):
        clear_cart(headers)
        pid, stock, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": stock + 100},
        )
        assert resp.status_code == 400

    def test_add_missing_product_id(self, headers):
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"quantity": 1},
        )
        assert resp.status_code in (400, 404)

    def test_add_missing_quantity(self, headers, admin_headers):
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid},
        )
        assert resp.status_code in (200, 400)
        # Server may default quantity to 0 or reject; either way document behavior

    def test_add_empty_body(self, headers):
        resp = requests.post(api_url("/cart/add"), headers=headers, json={})
        assert resp.status_code in (400, 404)

    def test_add_non_integer_quantity(self, headers, admin_headers):
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": "abc"},
        )
        assert resp.status_code == 400


class TestDuplicateAdd:
    """Adding the same product twice should SUM quantities, not replace."""

    def test_duplicate_add_sums_quantity(self, headers, admin_headers):
        clear_cart(headers)
        pid, stock, price = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        qty1, qty2 = 1, 2
        if stock < qty1 + qty2:
            pytest.skip("Not enough stock")

        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": qty1},
        )
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": qty2},
        )

        cart = requests.get(api_url("/cart"), headers=headers).json()
        items = cart.get("items", [])

        found = False
        for item in items:
            ipid = item.get("product_id")
            if ipid == pid:
                assert item.get("quantity") == qty1 + qty2, (
                    f"Expected quantity {qty1 + qty2}, got {item.get('quantity')}"
                )
                found = True
                break
        assert found, f"Product {pid} not found in cart"


class TestUpdateCart:
    """POST /cart/update — quantity must be >= 1."""

    def test_update_valid(self, headers, admin_headers):
        clear_cart(headers)
        pid, stock, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        resp = requests.post(
            api_url("/cart/update"), headers=headers,
            json={"product_id": pid, "quantity": 2},
        )
        assert resp.status_code == 200

    def test_update_zero_rejected(self, headers, admin_headers):
        clear_cart(headers)
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        resp = requests.post(
            api_url("/cart/update"), headers=headers,
            json={"product_id": pid, "quantity": 0},
        )
        assert resp.status_code == 400

    def test_update_negative_rejected(self, headers, admin_headers):
        clear_cart(headers)
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        resp = requests.post(
            api_url("/cart/update"), headers=headers,
            json={"product_id": pid, "quantity": -5},
        )
        assert resp.status_code == 400


class TestRemoveFromCart:
    """POST /cart/remove."""

    def test_remove_existing_item(self, headers, admin_headers):
        clear_cart(headers)
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        resp = requests.post(
            api_url("/cart/remove"), headers=headers,
            json={"product_id": pid},
        )
        assert resp.status_code == 200

    def test_remove_not_in_cart(self, headers):
        clear_cart(headers)
        resp = requests.post(
            api_url("/cart/remove"), headers=headers,
            json={"product_id": 999999},
        )
        assert resp.status_code == 404


class TestClearCart:
    def test_clear_cart(self, headers, admin_headers):
        pid, _, _ = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": 1},
        )
        resp = requests.delete(api_url("/cart/clear"), headers=headers)
        assert resp.status_code == 200

        cart = requests.get(api_url("/cart"), headers=headers).json()
        items = cart.get("items", [])
        assert len(items) == 0


class TestCartTotals:
    """Subtotal = qty × unit_price, total = sum of subtotals."""

    def test_subtotal_correct(self, headers, admin_headers):
        """Each item subtotal must equal quantity × unit_price."""
        clear_cart(headers)
        pid, stock, price = _get_first_active_product(admin_headers)
        if pid is None:
            pytest.skip("No products")
        qty = min(3, stock)
        requests.post(
            api_url("/cart/add"), headers=headers,
            json={"product_id": pid, "quantity": qty},
        )

        cart = requests.get(api_url("/cart"), headers=headers).json()
        items = cart.get("items", [])

        for item in items:
            if item.get("product_id") == pid:
                item_qty = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                subtotal = item.get("subtotal", 0)
                expected_sub = item_qty * unit_price
                assert abs(subtotal - expected_sub) < 0.01, (
                    f"Product {pid}: subtotal {subtotal} != {item_qty}×{unit_price}={expected_sub}"
                )

    def test_total_equals_sum_of_subtotals(self, headers, admin_headers):
        """Cart total must equal the sum of all item subtotals."""
        clear_cart(headers)
        resp = get_admin_products(admin_headers)
        products = resp.json()
        if isinstance(products, dict):
            products = products.get("products", [])

        # Add 2 different products
        added = 0
        expected_total = 0.0
        for p in products:
            if p.get("is_active") and p.get("stock_quantity", 0) > 0:
                pid = p["product_id"]
                requests.post(
                    api_url("/cart/add"), headers=headers,
                    json={"product_id": pid, "quantity": 1},
                )
                expected_total += p.get("price", 0)
                added += 1
                if added >= 2:
                    break

        cart = requests.get(api_url("/cart"), headers=headers).json()
        items = cart.get("items", [])
        cart_total = cart.get("total", 0)
        sum_subtotals = sum(item.get("subtotal", 0) for item in items)

        assert abs(cart_total - sum_subtotals) < 0.01, (
            f"Cart total {cart_total} != sum of subtotals {sum_subtotals}"
        )
