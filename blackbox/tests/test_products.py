"""
Test Products endpoints.
"""
import pytest
import requests
from conftest import api_url, get_admin_products


class TestListProducts:
    def test_list_products_success(self, headers):
        resp = requests.get(api_url("/products"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_only_active_products(self, headers, admin_headers):
        """Products list should only contain active products."""
        user_resp = requests.get(api_url("/products"), headers=headers)
        admin_resp = get_admin_products(admin_headers)
        assert user_resp.status_code == 200
        assert admin_resp.status_code == 200

        user_products = user_resp.json()
        admin_products = admin_resp.json()
        if isinstance(user_products, dict):
            user_products = user_products.get("products", [])
        if isinstance(admin_products, dict):
            admin_products = admin_products.get("products", [])

        inactive_ids = {
            p["product_id"] for p in admin_products if not p.get("is_active", True)
        }
        user_ids = {p["product_id"] for p in user_products}
        overlap = inactive_ids & user_ids
        assert len(overlap) == 0, f"Inactive products shown to user: {overlap}"


class TestGetProduct:
    def test_get_existing_product(self, headers, admin_headers):
        admin_resp = get_admin_products(admin_headers)
        products = admin_resp.json()
        if isinstance(products, dict):
            products = products.get("products", [])
        if not products:
            pytest.skip("No products in database")
        pid = products[0]["product_id"]
        resp = requests.get(api_url(f"/products/{pid}"), headers=headers)
        assert resp.status_code == 200

    def test_get_nonexistent_product(self, headers):
        resp = requests.get(api_url("/products/999999"), headers=headers)
        assert resp.status_code == 404

    def test_get_product_invalid_id(self, headers):
        resp = requests.get(api_url("/products/abc"), headers=headers)
        assert resp.status_code in (400, 404)


class TestProductFilters:
    """Filter, search, sort."""

    def test_filter_by_category(self, headers, admin_headers):
        admin_resp = get_admin_products(admin_headers)
        products = admin_resp.json()
        if isinstance(products, dict):
            products = products.get("products", [])
        if not products:
            pytest.skip("No products")
        cat = products[0].get("category")
        if not cat:
            pytest.skip("No category field")
        resp = requests.get(
            api_url("/products"), headers=headers, params={"category": cat}
        )
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("products", [])
        for p in data:
            assert p.get("category") == cat

    def test_search_by_name(self, headers, admin_headers):
        admin_resp = get_admin_products(admin_headers)
        products = admin_resp.json()
        if isinstance(products, dict):
            products = products.get("products", [])
        if not products:
            pytest.skip("No products")
        name = products[0].get("name", "")
        search_term = name.split()[0] if name else "Apple"
        resp = requests.get(
            api_url("/products"), headers=headers, params={"name": search_term}
        )
        assert resp.status_code == 200

    def test_sort_by_price_asc(self, headers):
        resp = requests.get(
            api_url("/products"), headers=headers, params={"sort": "price_asc"}
        )
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("products", [])
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices), "Products not sorted ascending by price"

    def test_sort_by_price_desc(self, headers):
        resp = requests.get(
            api_url("/products"), headers=headers, params={"sort": "price_desc"}
        )
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("products", [])
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices, reverse=True), "Products not sorted descending"


class TestProductPriceAccuracy:
    """Price shown must match admin database price."""

    def test_price_matches_admin(self, headers, admin_headers):
        admin_resp = get_admin_products(admin_headers)
        admin_products = admin_resp.json()
        if isinstance(admin_products, dict):
            admin_products = admin_products.get("products", [])

        user_resp = requests.get(api_url("/products"), headers=headers)
        user_products = user_resp.json()
        if isinstance(user_products, dict):
            user_products = user_products.get("products", [])

        admin_prices = {p["product_id"]: p["price"] for p in admin_products}
        for p in user_products:
            pid = p["product_id"]
            if pid in admin_prices:
                assert p["price"] == admin_prices[pid], (
                    f"Product {pid}: user price {p['price']} != admin price {admin_prices[pid]}"
                )
