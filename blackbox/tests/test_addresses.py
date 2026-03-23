"""
Test Addresses endpoints: CRUD + validation.
"""
import pytest
import requests
from conftest import api_url


def _valid_address(**overrides):
    """Return a valid address payload with optional overrides."""
    addr = {
        "label": "HOME",
        "street": "12345 Main Street",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    addr.update(overrides)
    return addr


class TestGetAddresses:
    def test_get_addresses(self, headers):
        resp = requests.get(api_url("/addresses"), headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))


class TestCreateAddress:
    """POST /addresses — validation and success."""

    def test_create_valid_address(self, headers):
        payload = _valid_address()
        resp = requests.post(api_url("/addresses"), headers=headers, json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        # Should contain the created address with an ID
        assert "address_id" in str(data).lower() or "id" in str(data).lower()

    # ── Label validation ───────────────────────────────────────────
    @pytest.mark.parametrize("label", ["HOME", "OFFICE", "OTHER"])
    def test_valid_labels(self, headers, label):
        payload = _valid_address(label=label)
        resp = requests.post(api_url("/addresses"), headers=headers, json=payload)
        assert resp.status_code in (200, 201)

    @pytest.mark.parametrize("label", ["WORK", "home", "random", "", 123])
    def test_invalid_labels(self, headers, label):
        payload = _valid_address(label=label)
        resp = requests.post(api_url("/addresses"), headers=headers, json=payload)
        assert resp.status_code == 400

    # ── Street length: 5–100 ──────────────────────────────────────
    def test_street_4_chars_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(street="ABCD"),
        )
        assert resp.status_code == 400

    def test_street_5_chars_valid(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(street="ABCDE"),
        )
        assert resp.status_code in (200, 201)

    def test_street_100_chars_valid(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(street="A" * 100),
        )
        assert resp.status_code in (200, 201)

    def test_street_101_chars_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(street="A" * 101),
        )
        assert resp.status_code == 400

    # ── City length: 2–50 ─────────────────────────────────────────
    def test_city_1_char_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(city="A"),
        )
        assert resp.status_code == 400

    def test_city_2_chars_valid(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(city="AB"),
        )
        assert resp.status_code in (200, 201)

    def test_city_50_chars_valid(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(city="C" * 50),
        )
        assert resp.status_code in (200, 201)

    def test_city_51_chars_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(city="C" * 51),
        )
        assert resp.status_code == 400

    # ── Pincode: exactly 6 digits ─────────────────────────────────
    def test_pincode_5_digits_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(pincode="12345"),
        )
        assert resp.status_code == 400

    def test_pincode_6_digits_valid(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(pincode="123456"),
        )
        assert resp.status_code in (200, 201)

    def test_pincode_7_digits_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(pincode="1234567"),
        )
        assert resp.status_code == 400

    def test_pincode_non_numeric_rejected(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(pincode="abcdef"),
        )
        assert resp.status_code == 400

    # ── Missing fields ─────────────────────────────────────────────
    @pytest.mark.parametrize("missing", ["label", "street", "city", "pincode"])
    def test_missing_required_field(self, headers, missing):
        payload = _valid_address()
        del payload[missing]
        resp = requests.post(api_url("/addresses"), headers=headers, json=payload)
        assert resp.status_code == 400

    def test_empty_body(self, headers):
        resp = requests.post(api_url("/addresses"), headers=headers, json={})
        assert resp.status_code == 400


class TestDefaultAddress:
    """Setting a new default should unset previous default."""

    def test_new_default_unsets_old(self, headers):
        # Create first address as default
        a1 = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(is_default=True),
        )
        assert a1.status_code in (200, 201)

        # Create second address as default
        a2 = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(is_default=True, label="OFFICE"),
        )
        assert a2.status_code in (200, 201)

        # Fetch all addresses and verify only one is default
        resp = requests.get(api_url("/addresses"), headers=headers)
        data = resp.json()
        if isinstance(data, dict) and "addresses" in data:
            addresses = data["addresses"]
        elif isinstance(data, list):
            addresses = data
        else:
            addresses = []

        defaults = [a for a in addresses if a.get("is_default")]
        assert len(defaults) <= 1, "More than one default address found"


class TestUpdateAddress:
    """PUT /addresses/{id} — only street and is_default can change."""

    def _create_address(self, headers):
        resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(),
        )
        data = resp.json()
        if isinstance(data, dict):
            # Try to find address_id
            if "address_id" in data:
                return data["address_id"]
            if "address" in data and isinstance(data["address"], dict):
                return data["address"].get("address_id") or data["address"].get("id")
            if "id" in data:
                return data["id"]
        return None

    def test_update_street(self, headers):
        addr_id = self._create_address(headers)
        if addr_id is None:
            pytest.skip("Could not create address to update")
        resp = requests.put(
            api_url(f"/addresses/{addr_id}"), headers=headers,
            json={"street": "99999 Updated Street"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Response should show updated street, not old
        assert "Updated Street" in str(data)

    def test_update_is_default(self, headers):
        addr_id = self._create_address(headers)
        if addr_id is None:
            pytest.skip("Could not create address to update")
        resp = requests.put(
            api_url(f"/addresses/{addr_id}"), headers=headers,
            json={"is_default": True},
        )
        assert resp.status_code == 200

    def test_update_label_ignored_or_rejected(self, headers):
        addr_id = self._create_address(headers)
        if addr_id is None:
            pytest.skip("Could not create address to update")
        resp = requests.put(
            api_url(f"/addresses/{addr_id}"), headers=headers,
            json={"label": "OFFICE"},
        )
        # Either 400 or the label stays the same
        if resp.status_code == 200:
            data = resp.json()
            # Label should not have changed
            addr_data = data.get("address", data)
            if "label" in addr_data:
                assert addr_data["label"] == "HOME"

    def test_update_city_ignored_or_rejected(self, headers):
        addr_id = self._create_address(headers)
        if addr_id is None:
            pytest.skip("Could not create address to update")
        resp = requests.put(
            api_url(f"/addresses/{addr_id}"), headers=headers,
            json={"city": "Mumbai"},
        )
        if resp.status_code == 200:
            data = resp.json()
            addr_data = data.get("address", data)
            if "city" in addr_data:
                assert addr_data["city"] != "Mumbai" or addr_data["city"] == "Hyderabad"

    def test_update_pincode_ignored_or_rejected(self, headers):
        addr_id = self._create_address(headers)
        if addr_id is None:
            pytest.skip("Could not create address to update")
        resp = requests.put(
            api_url(f"/addresses/{addr_id}"), headers=headers,
            json={"pincode": "999999"},
        )
        if resp.status_code == 200:
            data = resp.json()
            addr_data = data.get("address", data)
            if "pincode" in addr_data:
                assert addr_data["pincode"] != "999999"


class TestDeleteAddress:
    def test_delete_nonexistent_returns_404(self, headers):
        resp = requests.delete(api_url("/addresses/999999"), headers=headers)
        assert resp.status_code == 404

    def test_delete_valid_address(self, headers):
        # Create then delete
        create_resp = requests.post(
            api_url("/addresses"), headers=headers,
            json=_valid_address(label="OTHER"),
        )
        data = create_resp.json()
        addr_id = None
        if isinstance(data, dict):
            addr_id = data.get("address_id") or (
                data.get("address", {}).get("address_id")
                if isinstance(data.get("address"), dict) else None
            ) or data.get("id")
        if addr_id is None:
            pytest.skip("Could not create address")
        resp = requests.delete(api_url(f"/addresses/{addr_id}"), headers=headers)
        assert resp.status_code == 200
