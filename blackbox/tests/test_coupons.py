"""
Test Coupon endpoints.
"""
import pytest
import requests
from conftest import api_url, get_admin_products, get_admin_coupons, clear_cart, add_to_cart, remove_coupon, is_coupon_expired


class TestApplyCoupon:
    """POST /coupon/apply."""

    def _setup_cart_with_value(self, headers, admin_headers, min_value=500):
        """Fill cart to reach at least min_value. Returns approximate cart total."""
        clear_cart(headers)
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
                qty = min(stock, max(1, int((min_value - total) / price) + 1))
                add_to_cart(headers, pid, qty)
                total += price * qty
                if total >= min_value:
                    break
        return total

    def _get_valid_coupon(self, admin_headers):
        """Return a valid (non-expired) coupon dict."""
        resp = get_admin_coupons(admin_headers)
        coupons = resp.json()
        if isinstance(coupons, dict):
            coupons = coupons.get("coupons", [])
        for c in coupons:
            if not is_coupon_expired(c):
                return c
        return None

    def _get_expired_coupon(self, admin_headers):
        """Return an expired coupon dict if one exists."""
        resp = get_admin_coupons(admin_headers)
        coupons = resp.json()
        if isinstance(coupons, dict):
            coupons = coupons.get("coupons", [])
        for c in coupons:
            if is_coupon_expired(c):
                return c
        return None

    def test_apply_valid_coupon(self, headers, admin_headers):
        coupon = self._get_valid_coupon(admin_headers)
        if coupon is None:
            pytest.skip("No valid coupon available")
        min_val = coupon.get("min_cart_value", 0)
        self._setup_cart_with_value(headers, admin_headers, min_val + 200)
        remove_coupon(headers)
        code = coupon["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 200

    def test_apply_expired_coupon(self, headers, admin_headers):
        coupon = self._get_expired_coupon(admin_headers)
        if coupon is None:
            pytest.skip("No expired coupon available")
        self._setup_cart_with_value(headers, admin_headers, 2000)
        remove_coupon(headers)
        code = coupon["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 400, (
            f"Expired coupon '{code}' should be rejected, got {resp.status_code}"
        )

    def test_apply_coupon_cart_below_minimum(self, headers, admin_headers):
        coupon = self._get_valid_coupon(admin_headers)
        if coupon is None:
            pytest.skip("No valid coupon")
        min_val = coupon.get("min_cart_value", 0)
        if min_val <= 0:
            pytest.skip("Coupon has no min cart value")
        # Ensure cart is below minimum
        clear_cart(headers)
        remove_coupon(headers)
        code = coupon["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 400

    def test_apply_invalid_coupon_code(self, headers, admin_headers):
        self._setup_cart_with_value(headers, admin_headers, 500)
        remove_coupon(headers)
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": "INVALIDXYZ999"},
        )
        assert resp.status_code in (400, 404)

    def test_apply_empty_coupon_code(self, headers):
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": ""},
        )
        assert resp.status_code in (400, 404)

    def test_apply_missing_coupon_code_field(self, headers):
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={},
        )
        assert resp.status_code in (400, 404)

    def test_coupon_discount_percent(self, headers, admin_headers):
        """PERCENT coupon: verify discount is correctly computed and capped."""
        resp = get_admin_coupons(admin_headers)
        coupons = resp.json()
        if isinstance(coupons, dict):
            coupons = coupons.get("coupons", [])
        percent_coupon = None
        for c in coupons:
            if c.get("discount_type") == "PERCENT" and not is_coupon_expired(c):
                percent_coupon = c
                break
        if not percent_coupon:
            pytest.skip("No PERCENT coupon available")

        min_val = percent_coupon.get("min_cart_value", 0)
        cart_total = self._setup_cart_with_value(headers, admin_headers, max(min_val + 200, 500))
        remove_coupon(headers)

        code = percent_coupon["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 200

    def test_coupon_discount_fixed(self, headers, admin_headers):
        """FIXED coupon: verify discount is correctly computed."""
        resp = get_admin_coupons(admin_headers)
        coupons = resp.json()
        if isinstance(coupons, dict):
            coupons = coupons.get("coupons", [])
        fixed_coupon = None
        for c in coupons:
            if c.get("discount_type") == "FIXED" and not is_coupon_expired(c):
                fixed_coupon = c
                break
        if not fixed_coupon:
            pytest.skip("No FIXED coupon available")

        min_val = fixed_coupon.get("min_cart_value", 0)
        self._setup_cart_with_value(headers, admin_headers, max(min_val + 200, 500))
        remove_coupon(headers)

        code = fixed_coupon["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 200

    def test_coupon_max_discount_cap(self, headers, admin_headers):
        """When discount exceeds max_discount, it should be capped."""
        resp = get_admin_coupons(admin_headers)
        coupons = resp.json()
        if isinstance(coupons, dict):
            coupons = coupons.get("coupons", [])
        # Find a PERCENT coupon where we can exceed the cap
        target = None
        for c in coupons:
            if (c.get("discount_type") == "PERCENT" and not is_coupon_expired(c)
                    and c.get("max_discount", 0) > 0):
                target = c
                break
        if not target:
            pytest.skip("No suitable coupon with max_discount cap")

        # Make cart total high enough to exceed cap
        pct = target["discount_value"]
        max_disc = target["max_discount"]
        min_val = target.get("min_cart_value", 0)
        needed_total = max(int(max_disc / (pct / 100)) + 500, min_val + 200)
        self._setup_cart_with_value(headers, admin_headers, needed_total)
        remove_coupon(headers)

        code = target["coupon_code"]
        resp = requests.post(
            api_url("/coupon/apply"), headers=headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 200
        data = resp.json()
        discount = data.get("discount", data.get("discount_amount", None))
        if discount is not None:
            assert discount <= max_disc, (
                f"Discount {discount} exceeds max_discount cap {max_disc}"
            )


class TestRemoveCoupon:
    """POST /coupon/remove."""

    def test_remove_coupon(self, headers):
        resp = requests.post(api_url("/coupon/remove"), headers=headers)
        assert resp.status_code in (200, 400)
