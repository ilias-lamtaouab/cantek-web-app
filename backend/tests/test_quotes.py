"""Tests for the custom project quote feature. Gemini and email are always faked."""
import json
import secrets
from datetime import datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest

import ai_utils
from models import Product, Quote, QuoteTask, Setting

VALID_BODY = {
    "language": "en",
    "client_name": "Test Client",
    "client_email": "client@example.com",
    "description": "A website for my restaurant with an online menu and table reservations.",
}

GOOD_ANSWER = json.dumps({
    "tasks": [
        {"title": "Backend API", "description": "Menu and reservation API.", "estimated_days": 3.3},
        {"title": "Frontend", "description": "Public pages and admin pages.", "estimated_days": 2},
        {"title": "Testing", "description": "Manual and automated tests.", "estimated_days": 1},
    ]
})


class FakeGemini:
    """Plays a list of answers: a string is the model's text, an exception is raised."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0
        self.interactions = self

    def create(self, **kwargs):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(output_text=answer)


class FakeStatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


@pytest.fixture
def fake_gemini(monkeypatch):
    def install(*answers):
        fake = FakeGemini(answers)
        monkeypatch.setattr(ai_utils, "_new_client", lambda: fake)
        return fake
    return install


def make_quote(db, status="draft", language="en", email="client@example.com", days=(2.0, 3.5, 1.0),
               created_at=None, selected=None):
    quote = Quote(
        public_token=secrets.token_urlsafe(24),
        client_name="Test Client",
        client_email=email,
        description="Test project",
        language=language,
        status=status,
        created_at=created_at or datetime.utcnow(),
    )
    if status != "draft":
        quote.daily_rate = 400
        quote.total_days = sum(days)
        quote.total_price = sum(days) * 400
    db.add(quote)
    db.flush()
    tasks = []
    for position, task_days in enumerate(days):
        task = QuoteTask(
            quote_id=quote.id, position=position, title=f"Task {position}", description="Details",
            days=task_days, selected=status != "draft" if selected is None else selected,
        )
        db.add(task)
        tasks.append(task)
    db.commit()
    return quote, [task.id for task in tasks]


# ---------- POST /quotes/analyze ----------

def test_analyze_returns_checklist_and_saves_draft(client, db, fake_gemini):
    fake_gemini(GOOD_ANSWER)
    response = client.post("/quotes/analyze", json=VALID_BODY)

    assert response.status_code == 200
    data = response.json()
    assert len(data["quote_token"]) >= 30
    assert [task["days"] for task in data["tasks"]] == [3.5, 2.0, 1.0]  # rounded to half days
    assert "price" not in json.dumps(data)

    quote = db.query(Quote).one()
    assert quote.status == "draft"
    assert quote.total_price is None
    assert db.query(QuoteTask).count() == 3


@pytest.mark.parametrize("description", ["too short", "x" * 3001])
def test_analyze_limits_text_size(client, fake_gemini, description):
    fake = fake_gemini()
    response = client.post("/quotes/analyze", json={**VALID_BODY, "description": description})
    assert response.status_code == 422
    assert fake.calls == 0


def test_analyze_invalid_answer_is_retried_once(client, fake_gemini):
    fake = fake_gemini("not json", GOOD_ANSWER)
    response = client.post("/quotes/analyze", json=VALID_BODY)
    assert response.status_code == 200
    assert fake.calls == 2


def test_analyze_refuses_money_in_ai_answer(client, db, fake_gemini):
    with_price = json.dumps({"tasks": [
        {"title": "Backend API", "description": "API.", "estimated_days": 2, "price": 900}
    ]})
    fake = fake_gemini(with_price, with_price)
    response = client.post("/quotes/analyze", json={**VALID_BODY, "language": "fr"})

    assert response.status_code == 502
    assert "Veuillez réessayer plus tard" in response.json()["detail"]
    assert fake.calls == 2
    assert db.query(Quote).count() == 0


def test_analyze_retries_once_on_temporary_error(client, fake_gemini):
    fake = fake_gemini(FakeStatusError(503), GOOD_ANSWER)
    response = client.post("/quotes/analyze", json=VALID_BODY)
    assert response.status_code == 200
    assert fake.calls == 2


def test_analyze_retries_once_on_timeout(client, fake_gemini):
    timeout = httpx.ReadTimeout("slow")
    fake = fake_gemini(timeout, GOOD_ANSWER)
    response = client.post("/quotes/analyze", json=VALID_BODY)
    assert response.status_code == 200
    assert fake.calls == 2


@pytest.mark.parametrize("status_code, expected_status", [(429, 429), (401, 502), (403, 502)])
def test_analyze_never_retries_rate_limit_or_key_errors(client, fake_gemini, status_code, expected_status):
    fake = fake_gemini(FakeStatusError(status_code), GOOD_ANSWER)
    response = client.post("/quotes/analyze", json=VALID_BODY)
    assert response.status_code == expected_status
    assert fake.calls == 1


def test_analyze_free_tier_limit_message_in_french(client, fake_gemini):
    fake_gemini(FakeStatusError(429))
    response = client.post("/quotes/analyze", json={**VALID_BODY, "language": "fr"})
    assert response.status_code == 429
    assert response.json()["detail"].startswith("Trop de demandes")


def test_analyze_has_hard_time_limit(client, monkeypatch):
    import time

    class SlowGemini:
        interactions = None

        def __init__(self):
            self.interactions = self

        def create(self, **kwargs):
            time.sleep(3)

    monkeypatch.setattr(ai_utils, "_new_client", SlowGemini)
    monkeypatch.setattr(ai_utils, "AI_TOTAL_TIMEOUT_SECONDS", 1)
    started = time.monotonic()
    response = client.post("/quotes/analyze", json=VALID_BODY)

    assert response.status_code == 502
    assert time.monotonic() - started < 2.5


def test_analyze_rate_limit_per_ip(client, fake_gemini):
    fake_gemini(*[GOOD_ANSWER] * 5)
    for _ in range(5):
        assert client.post("/quotes/analyze", json=VALID_BODY).status_code == 200
    response = client.post("/quotes/analyze", json=VALID_BODY)
    assert response.status_code == 429
    assert response.json()["detail"].startswith("Too many requests")


# ---------- POST /quotes/submit ----------

def test_submit_computes_price_on_server_and_ignores_client_values(client, db):
    db.add(Setting(key="daily_rate", value="400"))
    db.commit()
    quote, task_ids = make_quote(db)

    response = client.post("/quotes/submit", json={
        "quote_token": quote.public_token,
        "task_ids": [task_ids[0], task_ids[1], task_ids[1]],  # duplicate id counted once
        "days": 0.1, "total_price": 1, "daily_rate": 1,
        "tasks": [{"title": "Free work", "days": 99}],
    })

    assert response.status_code == 200
    assert response.json()["total_days"] == 5.5
    db.refresh(quote)
    assert (quote.status, quote.daily_rate, quote.total_days, quote.total_price) == ("pending", 400, 5.5, 2200)
    selected = [task.selected for task in db.query(QuoteTask).order_by(QuoteTask.position)]
    assert selected == [True, True, False]
    assert db.query(QuoteTask).count() == 3


def test_submit_uses_default_rate_when_admin_never_set_one(client, db):
    quote, task_ids = make_quote(db)
    client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": [task_ids[0]]})
    db.refresh(quote)
    assert quote.daily_rate == 300
    assert quote.total_price == 600


def test_submit_token_cannot_be_reused(client, db):
    quote, task_ids = make_quote(db)
    body = {"quote_token": quote.public_token, "task_ids": [task_ids[0]]}
    assert client.post("/quotes/submit", json=body).status_code == 200
    assert client.post("/quotes/submit", json=body).status_code == 404


def test_submit_unknown_token_is_refused(client, db):
    make_quote(db)
    response = client.post("/quotes/submit", json={"quote_token": secrets.token_urlsafe(24), "task_ids": [1]})
    assert response.status_code == 404


def test_submit_expired_draft_is_refused(client, db):
    quote, task_ids = make_quote(db, created_at=datetime.utcnow() - timedelta(hours=3))
    response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": [task_ids[0]]})
    assert response.status_code == 404


def test_submit_refuses_invented_task(client, db):
    quote, task_ids = make_quote(db)
    _, other_task_ids = make_quote(db)
    for bad_ids in ([task_ids[0], other_task_ids[0]], [99999]):
        response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": bad_ids})
        assert response.status_code == 400
    db.refresh(quote)
    assert quote.status == "draft"


def test_submit_needs_at_least_one_task(client, db):
    quote, _ = make_quote(db)
    response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": []})
    assert response.status_code == 422


def test_pending_quote_limit_per_email(client, db):
    for _ in range(3):
        make_quote(db, status="pending")
    quote, task_ids = make_quote(db, language="fr")
    response = client.post("/quotes/submit", json={"quote_token": quote.public_token, "task_ids": [task_ids[0]]})
    assert response.status_code == 429
    assert "3 demandes de devis en attente" in response.json()["detail"]


# ---------- Daily rate setting ----------

def test_daily_rate_needs_login(client):
    assert client.get("/settings/daily-rate").status_code == 401
    assert client.put("/settings/daily-rate", json={"daily_rate": 500}).status_code == 401


def test_daily_rate_needs_admin(client, other_user_headers):
    response = client.put("/settings/daily-rate", json={"daily_rate": 500}, headers=other_user_headers)
    assert response.status_code == 403


@pytest.mark.parametrize("value", [0, -5, 100001, "abc"])
def test_daily_rate_refuses_invalid_values(client, admin_headers, value):
    response = client.put("/settings/daily-rate", json={"daily_rate": value}, headers=admin_headers)
    assert response.status_code == 422


def test_daily_rate_default_then_set(client, admin_headers):
    assert client.get("/settings/daily-rate", headers=admin_headers).json() == {"daily_rate": 300, "is_default": True}
    client.put("/settings/daily-rate", json={"daily_rate": 450}, headers=admin_headers)
    assert client.get("/settings/daily-rate", headers=admin_headers).json() == {"daily_rate": 450, "is_default": False}


# ---------- Admin quote routes ----------

@pytest.mark.parametrize("method, path", [("get", "/quotes"), ("put", "/quotes/1"), ("post", "/quotes/1/send")])
def test_admin_quote_routes_need_token(client, method, path):
    response = client.request(method.upper(), path, json={"daily_rate": 1, "tasks": []})
    assert response.status_code == 401


def test_admin_quote_routes_need_admin(client, db, other_user_headers):
    quote, _ = make_quote(db, status="pending")
    assert client.get("/quotes", headers=other_user_headers).status_code == 403
    assert client.post(f"/quotes/{quote.id}/send", headers=other_user_headers).status_code == 403


def test_admin_list_hides_drafts_and_shows_selected_tasks(client, db, admin_headers):
    make_quote(db)  # draft
    pending, _ = make_quote(db, status="pending", days=(2.0, 3.0))
    data = client.get("/quotes", headers=admin_headers).json()
    assert [quote["id"] for quote in data] == [pending.id]
    assert [task["days"] for task in data[0]["tasks"]] == [2.0, 3.0]


def test_admin_edit_recalculates_on_server(client, db, admin_headers):
    quote, task_ids = make_quote(db, status="pending", days=(2.0, 3.5))
    response = client.put(f"/quotes/{quote.id}", headers=admin_headers, json={
        "daily_rate": 500, "tasks": [{"id": task_ids[0], "days": 3}], "total_price": 1,
    })
    assert response.status_code == 200
    data = response.json()
    assert (data["daily_rate"], data["total_days"], data["total_price"]) == (500, 6.5, 3250)


@pytest.mark.parametrize("change", [
    {"daily_rate": 0, "tasks": []},
    {"daily_rate": 400, "tasks": [{"id": 1, "days": 0.3}]},
    {"daily_rate": 400, "tasks": [{"id": 1, "days": 61}]},
])
def test_admin_edit_refuses_invalid_values(client, db, admin_headers, change):
    quote, _ = make_quote(db, status="pending")
    assert client.put(f"/quotes/{quote.id}", headers=admin_headers, json=change).status_code == 422


def test_admin_edit_refuses_task_not_in_quote(client, db, admin_headers):
    quote, task_ids = make_quote(db, status="pending", selected=True)
    _, other_task_ids = make_quote(db, status="pending")
    for bad_id in (other_task_ids[0], 99999):
        response = client.put(f"/quotes/{quote.id}", headers=admin_headers, json={
            "daily_rate": 400, "tasks": [{"id": bad_id, "days": 2}],
        })
        assert response.status_code == 400


def test_admin_send_only_once_with_pdf(client, db, admin_headers, sent_emails):
    quote, task_ids = make_quote(db, status="pending", language="fr")

    first = client.post(f"/quotes/{quote.id}/send", headers=admin_headers)
    assert first.status_code == 200
    assert first.json()["status"] == "sent"
    assert first.json()["sent_at"] is not None

    second = client.post(f"/quotes/{quote.id}/send", headers=admin_headers)
    assert second.status_code == 400
    edit = client.put(f"/quotes/{quote.id}", headers=admin_headers,
                      json={"daily_rate": 1, "tasks": [{"id": task_ids[0], "days": 1}]})
    assert edit.status_code == 400

    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert email["To"] == "client@example.com"
    assert email["Subject"].startswith("Votre devis Cantek")
    attachment = next(email.iter_attachments())
    assert attachment.get_content_type() == "application/pdf"
    assert attachment.get_content().startswith(b"%PDF")


def test_admin_send_failure_keeps_quote_pending(client, db, admin_headers, monkeypatch):
    import email_utils

    def smtp_down(message):
        raise OSError("SMTP server down")

    monkeypatch.setattr(email_utils, "_send", smtp_down)
    quote, _ = make_quote(db, status="pending")
    response = client.post(f"/quotes/{quote.id}/send", headers=admin_headers)

    assert response.status_code == 502
    db.refresh(quote)
    assert quote.status == "pending"
    assert quote.sent_at is None


def test_admin_cannot_send_a_draft(client, db, admin_headers):
    quote, _ = make_quote(db)
    assert client.post(f"/quotes/{quote.id}/send", headers=admin_headers).status_code == 404


# ---------- Orders and quote-only services ----------

def test_quote_only_service_cannot_be_ordered(client, db):
    custom = Product(name="Custom Development", price=0, discount_percent=0, quote_only=True)
    normal = Product(name="IT Modernization", price=2500, discount_percent=0, quote_only=False)
    db.add_all([custom, normal])
    db.commit()
    order = {"client_name": "Client", "client_email": "client@example.com", "language": "en"}

    refused = client.post("/orders", json={**order, "product_id": custom.id})
    assert refused.status_code == 400

    accepted = client.post("/orders", json={**order, "product_id": normal.id})
    assert accepted.status_code == 200
    assert accepted.json()["total_price"] == 2500
