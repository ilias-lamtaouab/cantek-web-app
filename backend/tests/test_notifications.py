"""Admin notification emails for new orders and quote requests (fake email sender only)."""
import pytest

import email_utils
from models import Order, Product, Quote
from test_quotes import make_quote

SECRETS = ("test-secret-key", "fake-test-key")


@pytest.fixture
def normal_product(db):
    product = Product(name="IT Modernization", name_fr="Modernisation informatique", price=2500, discount_percent=10)
    db.add(product)
    db.commit()
    return product


@pytest.fixture
def smtp_down(monkeypatch):
    def fail(message):
        raise OSError("SMTP login failed for user secret@example.com")

    monkeypatch.setattr(email_utils, "_send", fail)


def plain_text(email):
    return email.get_body(("plain",)).get_content()


def order_body(product_id):
    return {
        "client_name": "Client Name", "client_email": "client@example.com",
        "product_id": product_id, "language": "fr", "total_price": 1,
    }


def test_new_order_emails_the_admins(client, normal_product, sent_emails):
    response = client.post("/orders", json=order_body(normal_product.id))
    assert response.status_code == 200
    order_id = response.json()["id"]

    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert email["To"] == "admin@example.com"
    assert email["Subject"] == f"New order CTK-{order_id:05d}"
    body = plain_text(email)
    assert "Modernisation informatique" in body
    assert "Client: Client Name" in body
    assert "Email: client@example.com" in body
    assert "$2,250.00" in body  # price from the database with its discount, not from the browser
    assert not any(secret in body for secret in SECRETS)


def test_quote_request_emails_the_admins(client, db, sent_emails):
    quote, task_ids = make_quote(db, days=(2.0, 3.5, 1.0))
    response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": task_ids[:2]})
    assert response.status_code == 200

    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert email["To"] == "admin@example.com"
    assert email["Subject"] == f"New quote request CTK-Q-{quote.id:05d}"
    body = plain_text(email)
    assert "Total days: 5.5" in body
    assert "Total: $1,650.00" in body  # 5.5 days x default rate 300
    assert "Client: Test Client" in body
    assert not any(secret in body for secret in SECRETS)


def test_admin_email_is_html_with_logo_table_and_button(client, normal_product, sent_emails):
    import email_utils

    response = client.post("/orders", json=order_body(normal_product.id))
    order_id = response.json()["id"]
    email = sent_emails[0]

    html = email.get_body(("html",)).get_content()
    assert "<table" in html
    assert f"CTK-{order_id:05d}" in html
    assert "client@example.com" in html
    assert "Open the admin" in html
    assert f'href="{email_utils.FRONTEND_URL}/admin"' in html
    assert not any(secret in html for secret in SECRETS)

    images = [part for part in email.walk() if part.get_content_type() == "image/png"]
    assert len(images) == 1
    cid = images[0]["Content-ID"].strip("<>")
    assert f'src="cid:{cid}"' in html

    # Plain-text fallback for mail apps without HTML
    assert email.get_body(("plain",)).get_content().startswith("A new order arrived.")


def test_client_text_is_escaped_in_html_email(client, normal_product, sent_emails):
    body = {**order_body(normal_product.id), "client_name": '<script>alert("x")</script>'}
    assert client.post("/orders", json=body).status_code == 200
    html = sent_emails[0].get_body(("html",)).get_content()
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_order_is_saved_when_admin_email_fails(client, db, normal_product, smtp_down, capsys):
    response = client.post("/orders", json=order_body(normal_product.id))

    assert response.status_code == 200
    assert db.query(Order).count() == 1
    output = capsys.readouterr().out
    assert "Admin notification email could not be sent" in output
    assert "secret@example.com" not in output  # only a generic message is logged


def test_quote_request_is_saved_when_admin_email_fails(client, db, smtp_down):
    quote, task_ids = make_quote(db)
    response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": [task_ids[0]]})

    assert response.status_code == 200
    db.refresh(quote)
    assert quote.status == "pending"


def test_refused_order_sends_no_email(client, db, sent_emails):
    custom = Product(name="Custom Development", price=0, discount_percent=0, quote_only=True)
    db.add(custom)
    db.commit()
    assert client.post("/orders", json=order_body(custom.id)).status_code == 400
    assert sent_emails == []
    assert db.query(Quote).count() == 0
