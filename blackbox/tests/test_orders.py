"""
Test Orders endpoints.
"""
import pytest
import requests
from conftest import api_url, get_admin_products, get_admin_orders, clear_cart, add_to_cart, remove_coupon


def _create_order(headers, admin_headers, payment="CARD"):
    """Create an order and return response data."""
    clear_cart(headers)
    remove_coupon(headers)
    resp = get_admin_products(admin_headers)
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", [])
    for p in products:
        if p.get("is_active") and p.get("stock_quantity", 0) > 0:
            add_to_cart(headers, p["product_id"], 1)
            break
    if payment == "WALLET":
        requests.post(api_url("/wallet/add"), headers=headers, json={"amount": 100000})
    resp = requests.post(api_url("/checkout"), headers=headers, json={"payment_method": payment})
    return resp.json() if resp.status_code == 200 else None


class TestListOrders:
    def test_list_orders(self, headers):
        resp = requests.get(api_url("/orders"), headers=headers)
        assert resp.status_code == 200


class TestGetOrder:
    def test_get_order_by_valid_id(self, headers, admin_headers):
        data = _create_order(headers, admin_headers)
        if data is None:
            pytest.skip("Could not create order")
        oid = data.get("order_id")
        resp = requests.get(api_url(f"/orders/{oid}"), headers=headers)
        assert resp.status_code == 200

    def test_get_nonexistent_order(self, headers):
        resp = requests.get(api_url("/orders/999999"), headers=headers)
        assert resp.status_code == 404


class TestCancelOrder:
    def test_cancel_valid_order(self, headers, admin_headers):
        data = _create_order(headers, admin_headers)
        if data is None:
            pytest.skip("Could not create order")
        oid = data.get("order_id")
        resp = requests.post(api_url(f"/orders/{oid}/cancel"), headers=headers)
        assert resp.status_code == 200

    def test_cancel_nonexistent_order(self, headers):
        resp = requests.post(api_url("/orders/999999/cancel"), headers=headers)
        assert resp.status_code == 404

    def test_cancel_already_cancelled_order(self, headers, admin_headers):
        data = _create_order(headers, admin_headers)
        if data is None:
            pytest.skip("Could not create order")
        oid = data.get("order_id")
        requests.post(api_url(f"/orders/{oid}/cancel"), headers=headers)
        resp = requests.post(api_url(f"/orders/{oid}/cancel"), headers=headers)
        assert resp.status_code == 400


class TestCancelDeliveredOrder:
    def test_cancel_delivered_returns_400(self, headers, admin_headers):
        resp = get_admin_orders(admin_headers)
        orders = resp.json()
        if isinstance(orders, dict):
            orders = orders.get("orders", [])
        delivered = None
        for o in (orders if isinstance(orders, list) else []):
            if o.get("order_status") == "DELIVERED":
                delivered = o
                break
        if delivered is None:
            pytest.skip("No delivered order")
        oid = delivered.get("order_id")
        resp = requests.post(api_url(f"/orders/{oid}/cancel"), headers=headers)
        assert resp.status_code == 400


class TestCancelStockRestoration:
    def test_stock_restored_on_cancel(self, headers, admin_headers):
        resp = get_admin_products(admin_headers)
        products = resp.json()
        if isinstance(products, dict):
            products = products.get("products", [])
        target = None
        for p in products:
            if p.get("is_active") and p.get("stock_quantity", 0) > 0:
                target = p
                break
        if target is None:
            pytest.skip("No suitable product")
        pid = target["product_id"]
        stock_before = target["stock_quantity"]

        clear_cart(headers)
        remove_coupon(headers)
        add_to_cart(headers, pid, 1)
        checkout_resp = requests.post(api_url("/checkout"), headers=headers, json={"payment_method": "CARD"})
        if checkout_resp.status_code != 200:
            pytest.skip("Checkout failed")
        oid = checkout_resp.json().get("order_id")

        # Cancel
        cancel_resp = requests.post(api_url(f"/orders/{oid}/cancel"), headers=headers)
        assert cancel_resp.status_code == 200

        # Check stock restored
        resp = get_admin_products(admin_headers)
        products_after = resp.json()
        if isinstance(products_after, dict):
            products_after = products_after.get("products", [])
        stock_after = None
        for p in products_after:
            if p["product_id"] == pid:
                stock_after = p["stock_quantity"]
                break
        assert stock_after == stock_before, (
            f"Stock not restored: before={stock_before}, after={stock_after}"
        )


class TestInvoice:
    def test_invoice_correctness(self, headers, admin_headers):
        data = _create_order(headers, admin_headers)
        if data is None:
            pytest.skip("Could not create order")
        oid = data.get("order_id")
        resp = requests.get(api_url(f"/orders/{oid}/invoice"), headers=headers)
        assert resp.status_code == 200
        inv = resp.json()
        subtotal = inv.get("subtotal", 0)
        gst = inv.get("gst_amount", 0)
        total = inv.get("total_amount", 0)
        expected_gst = subtotal * 0.05
        assert abs(gst - expected_gst) < 0.01, f"Invoice GST {gst} != {expected_gst}"
        assert abs(total - (subtotal + expected_gst)) < 0.01, f"Invoice total {total} != {subtotal + expected_gst}"

    def test_invoice_nonexistent_order(self, headers):
        resp = requests.get(api_url("/orders/999999/invoice"), headers=headers)
        assert resp.status_code == 404
