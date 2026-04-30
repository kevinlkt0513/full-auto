import pytest
from webui.backend.db import Database


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")


def test_create_and_verify_user(db):
    db.create_user("admin", "secret")
    assert db.verify_user("admin", "secret") is True
    assert db.verify_user("admin", "wrong") is False
    assert db.verify_user("nobody", "secret") is False


def test_user_count_distinguishes_uninitialized(db):
    assert db.user_count() == 0
    db.create_user("admin", "secret")
    assert db.user_count() == 1


def test_session_create_lookup_delete(db):
    db.create_user("admin", "secret")
    sid = db.create_session("admin")
    assert db.lookup_session(sid) == "admin"
    db.delete_session(sid)
    assert db.lookup_session(sid) is None


def test_session_expires(db, monkeypatch):
    import webui.backend.db as db_mod
    db.create_user("admin", "secret")
    times = [1000.0]
    monkeypatch.setattr(db_mod.time, "time", lambda: times[0])
    sid = db.create_session("admin", ttl_s=60)
    times[0] = 1061.0  # past TTL
    assert db.lookup_session(sid) is None
