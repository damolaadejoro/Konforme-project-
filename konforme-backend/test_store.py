"""Tests for the DynamoDB session layer (store.py)."""

import pytest

from models import Account, AccountControl, AuditLog, RemediationPlan, RemediationPlanMilestone, User
from store import IntegrityError, Session


def _account(db, email="owner@example.com"):
    account = Account(name="Acme", email=email)
    db.add(account)
    db.commit()
    return account


def test_add_commit_and_get(dynamodb):
    db = Session()
    account = _account(db)

    fresh = Session()
    loaded = fresh.get(Account, account.id)
    assert loaded is not None
    assert loaded.name == "Acme"
    assert loaded.is_active is True
    assert loaded.connected_at.tzinfo is not None


def test_lookup_by_email_and_token(dynamodb):
    db = Session()
    account = _account(db)
    user = User(account_id=account.id, name="Ann", email="ann@example.com", invite_token="tok-1")
    db.add(user)
    db.commit()

    fresh = Session()
    assert fresh.lookup(User, "email", "ann@example.com").id == user.id
    assert fresh.lookup(User, "invite_token", "tok-1").id == user.id
    assert fresh.lookup(User, "invite_token", "nope") is None


def test_updates_only_written_on_commit_and_rollback_reverts(dynamodb):
    db = Session()
    account = _account(db)

    s1 = Session()
    acc = s1.get(Account, account.id)
    acc.name = "Renamed"
    assert Session().get(Account, account.id).name == "Acme"
    s1.commit()
    assert Session().get(Account, account.id).name == "Renamed"

    acc.name = "Discarded"
    s1.rollback()
    assert acc.name == "Renamed"


def test_setting_field_to_none_removes_it(dynamodb):
    db = Session()
    account = _account(db)
    user = User(account_id=account.id, name="Ann", email="ann@example.com", invite_token="tok-1")
    db.add(user)
    db.commit()

    user.invite_token = None
    db.commit()

    fresh = Session()
    assert fresh.get(User, user.id).invite_token is None
    assert fresh.lookup(User, "invite_token", "tok-1") is None


def test_unique_email_enforced_and_freed_on_change(dynamodb):
    db = Session()
    _account(db, "a@example.com")
    with pytest.raises(IntegrityError):
        _account(Session(), "a@example.com")

    s = Session()
    acc = s.lookup(Account, "email", "a@example.com")
    acc.email = "b@example.com"
    s.commit()
    _account(Session(), "a@example.com")  # old address is free again


def test_composite_key_is_unique(dynamodb):
    db = Session()
    account = _account(db)
    db.add(AccountControl(account_id=account.id, control_id="ctrl-001"))
    db.commit()

    other = Session()
    other.add(AccountControl(account_id=account.id, control_id="ctrl-001"))
    with pytest.raises(IntegrityError):
        other.commit()
    assert Session().get_by_key(AccountControl, account.id, control_id="ctrl-001") is not None


def test_list_includes_pending_and_excludes_deleted(dynamodb):
    db = Session()
    account = _account(db)
    db.add_all([User(account_id=account.id, name=n, email=f"{n}@x.com") for n in ("a", "b")])
    db.commit()

    users = db.list(User, account.id)
    assert len(users) == 2
    db.delete(users[0])
    db.add(User(account_id=account.id, name="c", email="c@x.com"))
    assert sorted(u.name for u in db.list(User, account.id)) == sorted([users[1].name, "c"])
    db.commit()
    assert len(Session().list(User, account.id)) == 2


def test_delete_cascades_to_children(dynamodb):
    db = Session()
    account = _account(db)
    plan = RemediationPlan(account_id=account.id, title="Plan")
    db.add(plan)
    db.add_all([RemediationPlanMilestone(plan_id=plan.id, title=f"m{i}") for i in range(2)])
    db.commit()
    assert len(Session().get(RemediationPlan, plan.id).milestones) == 2

    s = Session()
    s.delete(s.get(RemediationPlan, plan.id))
    s.commit()
    assert Session().list(RemediationPlanMilestone, plan.id) == []


def test_delete_and_reinsert_same_key_in_one_commit(dynamodb):
    db = Session()
    account = _account(db)
    db.add(AccountControl(account_id=account.id, control_id="ctrl-001", status="Planned"))
    db.commit()

    s = Session()
    s.delete(s.get_by_key(AccountControl, account.id, control_id="ctrl-001"))
    s.add(AccountControl(account_id=account.id, control_id="ctrl-001", status="Implemented"))
    s.commit()
    assert Session().get_by_key(AccountControl, account.id, control_id="ctrl-001").status == "Implemented"


def test_audit_ids_increase_and_sort(dynamodb):
    db = Session()
    entries = [AuditLog(account_id="acc", event_type="e", event_category="c", hash="h") for _ in range(3)]
    db.add_all(entries)
    db.commit()
    ids = [e.id for e in entries]
    assert ids == sorted(ids) and len(set(ids)) == 3
    assert [e.id for e in Session().list(AuditLog, "acc")] == ids
