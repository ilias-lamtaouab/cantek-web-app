"""Automatic cleanup of old draft quotes."""
import threading
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import main
from models import Quote, QuoteTask
from test_quotes import make_quote


def days_ago(days):
    return datetime.utcnow() - timedelta(days=days)


def test_cleanup_deletes_only_drafts_older_than_7_days(db):
    old_draft, _ = make_quote(db, created_at=days_ago(8))
    recent_draft, _ = make_quote(db, created_at=days_ago(6))
    old_pending, _ = make_quote(db, status="pending", created_at=days_ago(30))
    old_sent, _ = make_quote(db, status="sent", created_at=days_ago(30))
    old_accepted, _ = make_quote(db, status="accepted", created_at=days_ago(30))
    kept = {recent_draft.id, old_pending.id, old_sent.id, old_accepted.id}
    old_draft_id = old_draft.id

    assert main.delete_old_drafts(db) == 1

    assert {quote.id for quote in db.query(Quote).all()} == kept
    assert db.query(QuoteTask).filter(QuoteTask.quote_id == old_draft_id).count() == 0
    assert {task.quote_id for task in db.query(QuoteTask).all()} == kept

    # Running it again changes nothing
    assert main.delete_old_drafts(db) == 0
    assert db.query(Quote).count() == 4


def test_cleanup_runs_when_the_backend_starts(db, monkeypatch):
    old_draft, _ = make_quote(db, created_at=days_ago(10))
    old_draft_id = old_draft.id
    finished = threading.Event()
    real_cleanup = main.delete_old_drafts

    def cleanup_and_signal(session):
        try:
            return real_cleanup(session)
        finally:
            finished.set()

    monkeypatch.setattr(main, "delete_old_drafts", cleanup_and_signal)
    with TestClient(main.app):  # starting the app runs the lifespan hook
        assert finished.wait(timeout=5)

    db.expire_all()
    assert db.get(Quote, old_draft_id) is None
