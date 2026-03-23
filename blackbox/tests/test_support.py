"""
Test Support Ticket endpoints.
"""
import pytest
import requests
from conftest import api_url


def _create_ticket(headers, subject="Test support ticket", message="I need help with my order"):
    """Create a support ticket and return the response data."""
    resp = requests.post(
        api_url("/support/ticket"), headers=headers,
        json={"subject": subject, "message": message},
    )
    return resp


class TestCreateTicket:
    """POST /support/ticket."""

    def test_create_valid_ticket(self, headers):
        resp = _create_ticket(headers)
        assert resp.status_code in (200, 201)

    # ── Subject boundaries: 5–100 ─────────────────────────────────
    def test_subject_4_chars_rejected(self, headers):
        resp = _create_ticket(headers, subject="ABCD")
        assert resp.status_code == 400

    def test_subject_5_chars_valid(self, headers):
        resp = _create_ticket(headers, subject="ABCDE")
        assert resp.status_code in (200, 201)

    def test_subject_100_chars_valid(self, headers):
        resp = _create_ticket(headers, subject="S" * 100)
        assert resp.status_code in (200, 201)

    def test_subject_101_chars_rejected(self, headers):
        resp = _create_ticket(headers, subject="S" * 101)
        assert resp.status_code == 400

    def test_subject_empty_rejected(self, headers):
        resp = _create_ticket(headers, subject="")
        assert resp.status_code == 400

    # ── Message boundaries: 1–500 ─────────────────────────────────
    def test_message_1_char_valid(self, headers):
        resp = _create_ticket(headers, message="X")
        assert resp.status_code in (200, 201)

    def test_message_500_chars_valid(self, headers):
        resp = _create_ticket(headers, message="M" * 500)
        assert resp.status_code in (200, 201)

    def test_message_empty_rejected(self, headers):
        resp = _create_ticket(headers, message="")
        assert resp.status_code == 400

    def test_message_501_chars_rejected(self, headers):
        resp = _create_ticket(headers, message="M" * 501)
        assert resp.status_code == 400

    # ── Missing fields ─────────────────────────────────────────────
    def test_missing_subject(self, headers):
        resp = requests.post(
            api_url("/support/ticket"), headers=headers,
            json={"message": "No subject"},
        )
        assert resp.status_code == 400

    def test_missing_message(self, headers):
        resp = requests.post(
            api_url("/support/ticket"), headers=headers,
            json={"subject": "No message here"},
        )
        assert resp.status_code == 400

    def test_empty_body(self, headers):
        resp = requests.post(
            api_url("/support/ticket"), headers=headers,
            json={},
        )
        assert resp.status_code == 400


class TestTicketInitialStatus:
    """New ticket always starts OPEN."""

    def test_initial_status_open(self, headers):
        resp = _create_ticket(headers, subject="Check status")
        assert resp.status_code in (200, 201)
        data = resp.json()
        ticket = data.get("ticket", data)
        status = ticket.get("status", "")
        assert status == "OPEN", f"Expected OPEN, got {status}"


class TestTicketMessagePreservation:
    """Full message must be saved exactly as written."""

    def test_message_preserved_exactly(self, headers):
        msg = "Hello! I need help with order #12345. [Special chars: @#$%^&*()]"
        resp = _create_ticket(headers, subject="Exact message test", message=msg)
        assert resp.status_code in (200, 201)
        data = resp.json()
        ticket = data.get("ticket", data)
        saved_msg = ticket.get("message", ticket.get("description", ""))
        assert saved_msg == msg, f"Message not preserved: '{saved_msg}' != '{msg}'"


class TestGetTickets:
    def test_get_tickets(self, headers):
        resp = requests.get(api_url("/support/tickets"), headers=headers)
        assert resp.status_code == 200


class TestUpdateTicketStatus:
    """PUT /support/tickets/{id} — status transitions."""

    def _create_and_get_id(self, headers):
        resp = _create_ticket(headers, subject="Status transition test")
        if resp.status_code not in (200, 201):
            return None
        data = resp.json()
        ticket = data.get("ticket", data)
        return ticket.get("ticket_id") or ticket.get("id")

    def test_open_to_in_progress(self, headers):
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        assert resp.status_code == 200

    def test_in_progress_to_closed(self, headers):
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        # First move to IN_PROGRESS
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        # Then CLOSED
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "CLOSED"},
        )
        assert resp.status_code == 200

    def test_open_to_closed_rejected(self, headers):
        """OPEN cannot go directly to CLOSED."""
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "CLOSED"},
        )
        assert resp.status_code == 400

    def test_closed_to_open_rejected(self, headers):
        """CLOSED cannot go back to OPEN."""
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        # Move through: OPEN → IN_PROGRESS → CLOSED
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "CLOSED"},
        )
        # Try to reopen
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "OPEN"},
        )
        assert resp.status_code == 400

    def test_closed_to_in_progress_rejected(self, headers):
        """CLOSED cannot go back to IN_PROGRESS."""
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "CLOSED"},
        )
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        assert resp.status_code == 400

    def test_in_progress_to_open_rejected(self, headers):
        """IN_PROGRESS cannot go back to OPEN."""
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "IN_PROGRESS"},
        )
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "OPEN"},
        )
        assert resp.status_code == 400

    def test_invalid_status_value(self, headers):
        tid = self._create_and_get_id(headers)
        if tid is None:
            pytest.skip("Could not create ticket")
        resp = requests.put(
            api_url(f"/support/tickets/{tid}"), headers=headers,
            json={"status": "INVALID_STATUS"},
        )
        assert resp.status_code == 400
