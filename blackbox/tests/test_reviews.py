"""
Test Reviews endpoints.
"""
import pytest
import requests
from conftest import api_url, get_admin_products


def _get_active_pid(admin_headers):
    resp = get_admin_products(admin_headers)
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", [])
    for p in products:
        if p.get("is_active"):
            return p["product_id"]
    return None


class TestGetReviews:
    def test_get_reviews_valid(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if pid is None:
            pytest.skip("No products")
        resp = requests.get(api_url(f"/products/{pid}/reviews"), headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "reviews" in data
        assert "average_rating" in data


class TestAddReview:
    def test_valid_review(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 4, "comment": "Great!"})
        assert resp.status_code in (200, 201)

    def test_rating_1(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 1, "comment": "Poor"})
        assert resp.status_code in (200, 201)

    def test_rating_5(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 5, "comment": "Best"})
        assert resp.status_code in (200, 201)

    def test_rating_0_rejected(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 0, "comment": "Bad"})
        assert resp.status_code == 400

    def test_rating_6_rejected(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 6, "comment": "Over"})
        assert resp.status_code == 400

    def test_rating_negative(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": -1, "comment": "Bad"})
        assert resp.status_code == 400

    def test_rating_non_integer(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": "five", "comment": "Hmm"})
        assert resp.status_code == 400

    def test_comment_1_char(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 3, "comment": "A"})
        assert resp.status_code in (200, 201)

    def test_comment_200_chars(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 3, "comment": "A" * 200})
        assert resp.status_code in (200, 201)

    def test_comment_empty_rejected(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 3, "comment": ""})
        assert resp.status_code == 400

    def test_comment_201_rejected(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 3, "comment": "B" * 201})
        assert resp.status_code == 400

    def test_missing_rating(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"comment": "No rating"})
        assert resp.status_code == 400

    def test_missing_comment(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 4})
        assert resp.status_code == 400

    def test_empty_body(self, headers, admin_headers):
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        resp = requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={})
        assert resp.status_code == 400


class TestAverageRating:
    def test_average_is_proper_decimal(self, headers, admin_headers):
        """Average rating must be a proper decimal, not truncated integer."""
        pid = _get_active_pid(admin_headers)
        if not pid: pytest.skip("No products")
        # Add reviews with different ratings to produce a non-integer average
        requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 2, "comment": "Low"})
        requests.post(api_url(f"/products/{pid}/reviews"), headers=headers, json={"rating": 5, "comment": "High"})

        resp = requests.get(api_url(f"/products/{pid}/reviews"), headers=headers)
        data = resp.json()
        avg = data.get("average_rating")
        reviews = data.get("reviews", [])
        if len(reviews) > 1:
            ratings = [r["rating"] for r in reviews]
            expected = sum(ratings) / len(ratings)
            assert abs(avg - expected) < 0.01, (
                f"Average {avg} != expected {expected}. Appears truncated to integer."
            )
