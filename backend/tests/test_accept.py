"""Accepting a quote online with the one-time link (fake email sender only)."""
import re
import secrets
from datetime import datetime, timedelta

import pytest

from models import Order, Product, Quote
from test_quotes import make_quote


@pytest.fixture
def custom_product(db):
    product = Product(name="Custom Development", name_fr="Développement sur mesure",
                      price=0, discount_percent=0, quote_only=True)
    db.add(product)
    db.commit()
    return product


@pytest.fixture
def sent_quote(client, db, admin_headers, sent_emails, custom_product):
    """A quote sent by the admin through the real route. Returns (quote, token from the email)."""
    quote, _ = make_quote(db, status="pending", language="fr", days=(2.0, 3.5))
    response = client.post(f"/quotes/{quote.id}/send", headers=admin_headers)
    assert response.status_code == 200
    body = sent_emails[-1].get_body(("plain",)).get_content()
    token = re.search(r"/accept-quote\?token=([\w-]+)", body).group(1)
    sent_emails.clear()
    db.refresh(quote)
    return quote, token


def test_send_creates_separate_long_token_valid_30_days(sent_quote, sent_emails):
    quote, token = sent_quote
    assert len(token) >= 40
    assert token != quote.public_token
    assert quote.accept_token == token
    days_valid = (quote.accept_token_expires_at - quote.sent_at).days
    assert days_valid == 30


def test_quote_email_and_pdf_contain_the_accept_link(client, db, admin_headers, sent_emails):
    quote, _ = make_quote(db, status="pending", language="en")
    client.post(f"/quotes/{quote.id}/send", headers=admin_headers)
    email = sent_emails[-1]
    body = email.get_body(("plain",)).get_content()
    assert "Accept this quote" in body
    link = re.search(r"http\S+/accept-quote\?token=[\w-]+", body).group(0)
    pdf = next(email.iter_attachments()).get_content()
    assert link.encode() in pdf


def test_preview_shows_summary_only(client, sent_quote):
    quote, token = sent_quote
    response = client.post("/quotes/accept/preview", json={"token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["quote_number"] == f"CTK-Q-{quote.id:05d}"
    assert [task["days"] for task in data["tasks"]] == [2.0, 3.5]
    assert (data["total_days"], data["daily_rate"], data["total_price"]) == (5.5, 400, 2200)
    assert data["language"] == "fr"
    text = response.text
    assert token not in text and quote.public_token not in text and "@" not in text


def test_accept_creates_one_pending_order_with_quote_total(client, db, sent_quote, custom_product, sent_emails):
    quote, token = sent_quote
    response = client.post("/quotes/accept", json={
        "token": token, "total_price": 1, "daily_rate": 1, "days": 0.5,
    })
    assert response.status_code == 200

    order = db.query(Order).one()
    assert response.json() == {
        "quote_number": f"CTK-Q-{quote.id:05d}",
        "order_number": f"CTK-{order.id:05d}",
        "total_price": 2200,
    }
    assert order.status == "pending"
    assert (order.unit_price, order.discount_percent, order.total_price) == (2200, 0, 2200)
    assert order.service_name == f"Développement sur mesure (devis CTK-Q-{quote.id:05d})"
    assert order.product_id == custom_product.id
    assert order.language == "fr"
    assert (order.client_name, order.client_email) == (quote.client_name, quote.client_email)

    db.refresh(quote)
    assert quote.status == "accepted"
    assert quote.accepted_at is not None
    assert quote.order_id == order.id

    # The admins are told (feature A)
    assert len(sent_emails) == 1
    assert sent_emails[0]["Subject"] == f"Quote CTK-Q-{quote.id:05d} accepted, new order CTK-{order.id:05d}"


def test_link_works_only_once(client, db, sent_quote):
    _, token = sent_quote
    assert client.post("/quotes/accept", json={"token": token}).status_code == 200
    second = client.post("/quotes/accept", json={"token": token})
    assert second.status_code == 409
    assert client.post("/quotes/accept/preview", json={"token": token}).status_code == 409
    assert db.query(Order).count() == 1


def test_two_requests_racing_create_only_one_order(client, db, sent_quote, monkeypatch):
    """Both requests pass the first check before either one saves (as when they arrive together).
    The atomic "sent -> accepted" update must still let only one of them create an order."""
    import main

    quote, token = sent_quote
    first = client.post("/quotes/accept", json={"token": token})

    # Second request whose first check ran before the first request saved: skip that check.
    monkeypatch.setattr(main, "find_quote_to_accept", lambda session, t: session.get(Quote, quote.id))
    second = client.post("/quotes/accept", json={"token": token})

    assert first.status_code == 200
    assert second.status_code == 409
    assert db.query(Order).count() == 1


@pytest.mark.parametrize("token", ["", "x" * 201])
def test_malformed_token_is_refused(client, token):
    assert client.post("/quotes/accept", json={"token": token}).status_code == 422


def test_unknown_token_does_nothing(client, db, sent_quote):
    unknown = secrets.token_urlsafe(32)
    assert client.post("/quotes/accept/preview", json={"token": unknown}).status_code == 404
    assert client.post("/quotes/accept", json={"token": unknown}).status_code == 404
    assert db.query(Order).count() == 0


def test_public_token_cannot_be_used_to_accept(client, db, sent_quote):
    quote, _ = sent_quote
    assert client.post("/quotes/accept", json={"token": quote.public_token}).status_code == 404
    assert db.query(Order).count() == 0


def test_expired_link_does_nothing(client, db, sent_quote):
    quote, token = sent_quote
    quote.accept_token_expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    assert client.post("/quotes/accept/preview", json={"token": token}).status_code == 410
    assert client.post("/quotes/accept", json={"token": token}).status_code == 410
    db.refresh(quote)
    assert quote.status == "sent"
    assert db.query(Order).count() == 0


@pytest.mark.parametrize("status", ["draft", "pending"])
def test_link_works_only_for_sent_quotes(client, db, status):
    quote, _ = make_quote(db, status=status)
    quote.accept_token = secrets.token_urlsafe(32)
    quote.accept_token_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    assert client.post("/quotes/accept", json={"token": quote.accept_token}).status_code == 404
    assert db.query(Order).count() == 0


def test_accepted_quote_cannot_be_edited_or_sent_again(client, db, sent_quote, admin_headers, sent_emails):
    quote, token = sent_quote
    client.post("/quotes/accept", json={"token": token})
    sent_emails.clear()

    assert client.post(f"/quotes/{quote.id}/send", headers=admin_headers).status_code == 400
    edit = client.put(f"/quotes/{quote.id}", headers=admin_headers, json={"daily_rate": 1, "tasks": []})
    assert edit.status_code == 400
    assert sent_emails == []


def test_admin_list_shows_accepted_status_and_order(client, db, sent_quote, admin_headers):
    quote, token = sent_quote
    client.post("/quotes/accept", json={"token": token})
    order = db.query(Order).one()

    data = client.get("/quotes", headers=admin_headers).json()
    assert data[0]["status"] == "accepted"
    assert data[0]["order_id"] == order.id
    assert data[0]["accepted_at"] is not None
    assert "accept_token" not in data[0]


def test_accepted_quote_order_can_be_confirmed_as_usual(client, db, sent_quote, admin_headers, sent_emails):
    _, token = sent_quote
    client.post("/quotes/accept", json={"token": token})
    order = db.query(Order).one()
    sent_emails.clear()

    response = client.put(f"/orders/{order.id}/confirm", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    confirmation = sent_emails[-1]
    assert confirmation["Subject"].startswith("Votre commande Cantek")
    assert next(confirmation.iter_attachments()).get_content().startswith(b"%PDF")


def test_accept_works_without_a_quote_only_service(client, db, admin_headers, sent_emails):
    quote, _ = make_quote(db, status="pending", language="en")
    client.post(f"/quotes/{quote.id}/send", headers=admin_headers)
    db.refresh(quote)
    assert client.post("/quotes/accept", json={"token": quote.accept_token}).status_code == 200
    order = db.query(Order).one()
    assert order.product_id is None
    assert order.service_name == f"Custom Development (quote CTK-Q-{quote.id:05d})"
