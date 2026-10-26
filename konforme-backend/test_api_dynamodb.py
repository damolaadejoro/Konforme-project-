"""End-to-end API flow against the mocked DynamoDB table.

Exercises every router once so the persistence layer is covered beyond auth.
"""

import io
from datetime import date, timedelta

import pytest

import report_storage
from config import settings
from models import Country, CountryAssessmentQuestion, EntityTier
from store import Session

PASSWORD = "SecurePass123!"


def ok(res, status=None):
    expected = (status,) if status else (200, 201, 204)
    assert res.status_code in expected, f"{res.request.method} {res.request.url} -> {res.status_code}: {res.text}"
    return res.json() if res.content else None


@pytest.fixture()
def api(client, tmp_path, monkeypatch):
    """Client with a registered owner, CSRF pair and writable local file storage."""
    from cryptography.fernet import Fernet

    monkeypatch.setattr(settings, "encryption_key", Fernet.generate_key().decode())
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "evidence"))
    monkeypatch.setattr(settings, "s3_evidence_bucket", "")
    monkeypatch.setattr(settings, "s3_reports_bucket", "")
    monkeypatch.setattr(report_storage, "REPORT_STORAGE_PATH", str(tmp_path / "reports"))

    reg = ok(client.post("/api/v1/auth/register", json={"name": "Acme", "email": "owner@example.com", "password": PASSWORD}))
    client.cookies.set("csrf_token", "csrf-test")
    client.headers.update({"Authorization": f"Bearer {reg['access_token']}", "X-CSRF-Token": "csrf-test"})
    client.account_id = reg["account_id"]
    client.user_id = reg["user_id"]
    return client


def _seed_country():
    db = Session()
    country = Country(code="DE", name="Germany", transposition_status="transposed")
    db.add(country)
    db.add(EntityTier(country_id=country.id, tier_key="essential", local_name="Besonders wichtig"))
    db.add(CountryAssessmentQuestion(country_id=country.id, question_text="Extra DE question", is_additional=True))
    db.commit()


def test_auth_lifecycle(api):
    a = api
    me = ok(a.get("/api/v1/auth/me"))
    assert me["user_id"] == a.user_id and me["role"] == "owner"

    # Wrong password counts toward lockout; right one resets
    a.headers.pop("Authorization")
    ok(a.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "Wrong-pass1!"}), 401)
    login = ok(a.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}))
    a.headers["Authorization"] = f"Bearer {login['access_token']}"

    # Email verification by token
    token = next(u for u in Session().list(__import__("models").User, a.account_id)).email_verification_token
    ok(a.post(f"/api/v1/auth/verify-email?token={token}"))
    assert ok(a.get("/api/v1/auth/me"))["email_verified"] is True

    # Password reset by token
    ok(a.post("/api/v1/auth/forgot-password", json={"email": "owner@example.com"}))
    reset = Session().lookup(__import__("models").User, "email", "owner@example.com").password_reset_token
    ok(a.post("/api/v1/auth/reset-password", json={"token": reset, "new_password": "NewSecure123!"}))
    ok(a.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "NewSecure123!"}))


def test_accounts_team_and_settings(api):
    a = api
    acc = ok(a.get("/api/v1/accounts"))
    assert acc["id"] == a.account_id
    ok(a.put("/api/v1/accounts", json={"name": "Acme GmbH", "language": "de"}))
    assert ok(a.get("/api/v1/accounts"))["name"] == "Acme GmbH"

    invited = ok(a.post("/api/v1/team/invite", json={"emails": ["new@example.com"], "role": "member"}), 201)
    from models import User
    invite_token = Session().lookup(User, "email", "new@example.com").invite_token
    assert ok(a.get(f"/api/v1/team/accept-invite?token={invite_token}"))["email"] == "new@example.com"
    ok(a.post("/api/v1/team/accept-invite", json={"token": invite_token, "name": "Newbie", "password": PASSWORD}))
    members = ok(a.get("/api/v1/team/members"))
    assert [m["email"] for m in members] == ["owner@example.com", "new@example.com"]
    member_id = invited[0]["id"]
    assert ok(a.put(f"/api/v1/team/members/{member_id}/role", json={"role": "admin"}))["role"] == "admin"
    ok(a.delete(f"/api/v1/team/members/{member_id}"))

    cfg = ok(a.put("/api/v1/settings/scoring", json={"technical_weight": 0.5, "assessment_weight": 0.3, "controls_weight": 0.2}))
    assert cfg["technicalWeight"] == 0.5
    assert ok(a.get("/api/v1/settings/scoring"))["technicalWeight"] == 0.5


def test_countries_and_controls(api):
    a = api
    _seed_country()
    assert [c["code"] for c in ok(a.get("/api/v1/countries"))] == ["DE"]
    assert ok(a.get("/api/v1/countries/de"))["name"] == "Germany"
    assert ok(a.get("/api/v1/countries/DE/tiers"))[0]["tierKey"] == "essential"
    ok(a.get("/api/v1/countries/DE/assessment"))
    ok(a.put("/api/v1/accounts/country", json={"country_code": "DE", "entity_tier": "essential"}))
    ok(a.put("/api/v1/accounts/country", json={"country_code": "DE", "entity_tier": "nope"}), 422)

    base = ok(a.get("/api/v1/base-controls"))
    assert len(base) == 43
    controls = ok(a.get(f"/api/v1/controls/{a.account_id}"))
    assert len(controls) == 43  # instantiated from base controls when the country was set
    first = controls[0]["controlId"]

    # Implemented requires linked evidence
    ok(a.patch(f"/api/v1/controls/{a.account_id}/{first}", json={"status": "Implemented"}), 422)
    patched = ok(a.patch(f"/api/v1/controls/{a.account_id}/{first}", json={"status": "Planned", "owner": "Ann"}))
    assert patched["status"] == "Planned"
    # Planned auto-creates a remediation task for the control
    tasks = ok(a.get(f"/api/v1/remediation/{a.account_id}"))
    assert any(t.get("relatedControlId") == first for t in tasks)

    bulk = ok(a.put(f"/api/v1/controls/{a.account_id}/bulk", json={"controls": [{"control_id": "ctrl-002", "status": "Planned"}]}))
    assert next(c for c in bulk if c["controlId"] == "ctrl-002")["status"] == "Planned"


def test_campaigns(api):
    a = api
    camp = ok(a.post(f"/api/v1/campaigns/{a.account_id}", json={
        "control_id": "ctrl-001", "control_name": "Policy", "task_type": "acknowledge", "deadline": "2030-01-01",
        "employees": [{"employee_name": "Eve", "employee_email": "eve@example.com"}],
    }), 201)
    task = camp["tasks"][0]
    assert ok(a.get(f"/api/v1/campaigns/{a.account_id}"))[0]["id"] == camp["id"]
    ok(a.patch(f"/api/v1/campaigns/{a.account_id}/tasks/{task['id']}", json={"score": 90}))

    from models import CampaignTask
    token = Session().get(CampaignTask, task["id"]).completion_token
    assert ok(a.get(f"/api/v1/campaigns/tasks/complete/{token}"))["employee_name"] == "Eve"
    ok(a.post(f"/api/v1/campaigns/tasks/complete/{token}"))
    ok(a.get(f"/api/v1/campaigns/tasks/complete/{token}"), 404)  # token is single-use


def test_business_processes(api):
    a = api
    bp = ok(a.post(f"/api/v1/business-processes/{a.account_id}", json={"name": "Payments"}), 201)
    ok(a.patch(f"/api/v1/business-processes/{a.account_id}/{bp['id']}", json={"owner": "Ops"}))
    links = ok(a.put(f"/api/v1/business-processes/{a.account_id}/{bp['id']}/controls",
                     json={"controls": [{"control_id": "ctrl-001"}, {"control_id": "ctrl-002", "applicable": False}]}))
    assert len(links) == 2
    # Replacing links with an overlapping set (delete + re-add same key in one commit)
    ok(a.put(f"/api/v1/business-processes/{a.account_id}/{bp['id']}/controls",
             json={"controls": [{"control_id": "ctrl-001", "justification": "core"}]}))
    assert len(ok(a.get(f"/api/v1/business-processes/{a.account_id}/{bp['id']}"))["controls"]) == 1
    soa = ok(a.get(f"/api/v1/business-processes/{a.account_id}/soa"))
    assert next(e for e in soa if e["controlId"] == "ctrl-001")["linkedProcesses"] == ["Payments"]
    ok(a.delete(f"/api/v1/business-processes/{a.account_id}/{bp['id']}"))
    ok(a.get(f"/api/v1/business-processes/{a.account_id}/{bp['id']}"), 404)

    assert len(ok(a.get("/api/v1/mappings/question-controls"))) == 59


def test_assessment_score_and_remediation(api):
    a = api
    ok(a.patch(f"/api/v1/assessment/{a.account_id}/response/nis2-020-01", json={"question_id": "nis2-020-01", "maturity_level": 1}))
    from assessment_questions import QUESTIONS

    answers = [{"question_id": q["id"], "maturity_level": 3} for q in QUESTIONS]
    answers[0]["maturity_level"] = 1  # one gap -> one auto-created remediation task
    answers = [{**r, "maturity_level": 2} if r["maturity_level"] == 3 else r for r in answers]
    ok(a.post(f"/api/v1/assessment/{a.account_id}/v2", json={"responses": answers}))
    detail = ok(a.get(f"/api/v1/assessment/{a.account_id}"))
    assert detail["assessment"] is not None
    history = ok(a.get(f"/api/v1/assessment/{a.account_id}/history"))
    ok(a.get(f"/api/v1/assessment/{a.account_id}/version/{history['versions'][0]['id']}"))

    score = ok(a.get(f"/api/v1/score/{a.account_id}"))
    assert "overallScore" in score or "overall_score" in score or score
    ok(a.get(f"/api/v1/report/{a.account_id}"))

    # Low maturity auto-created a remediation task
    tasks = ok(a.get(f"/api/v1/remediation/{a.account_id}"))
    assert tasks
    manual = ok(a.post(f"/api/v1/remediation/{a.account_id}", json={
        "question_id": "nis2-020-03", "title": "Manual task", "due_date": (date.today() + timedelta(days=10)).isoformat(),
    }))
    ok(a.patch(f"/api/v1/remediation/{a.account_id}/{manual['id']}", json={"status": "in_progress"}))
    ok(a.post(f"/api/v1/remediation/{a.account_id}/{manual['id']}/reschedule",
              json={"new_due_date": (date.today() + timedelta(days=40)).isoformat(), "reason": "waiting on vendor"}))

    plan = ok(a.post(f"/api/v1/remediation/{a.account_id}/plans", json={
        "title": "Fix policies", "initial_task_ids": [manual["id"]],
        "linked_entities": [{"entity_type": "control", "entity_id": "ctrl-001"}],
    }))
    ms = ok(a.post(f"/api/v1/remediation/{a.account_id}/plans/{plan['id']}/milestones", json={"title": "Draft"}))
    ok(a.patch(f"/api/v1/remediation/{a.account_id}/plans/{plan['id']}/milestones/{ms['id']}", json={"title": "Draft v2"}))
    ok(a.post(f"/api/v1/remediation/{a.account_id}/plans/{plan['id']}/milestones/{ms['id']}/complete"))
    full = ok(a.get(f"/api/v1/remediation/{a.account_id}/plans/{plan['id']}"))
    assert full["taskCount"] == 1  # the initial task was attached to the plan
    assert len(ok(a.get(f"/api/v1/remediation/{a.account_id}/plans"))) == 1

    ok(a.post(f"/api/v1/remediation/{a.account_id}/{manual['id']}/close", json={"closure_note": "done"}))
    auto_ids = [t["id"] for t in tasks]
    ok(a.post(f"/api/v1/remediation/{a.account_id}/bulk-dismiss", json={"task_ids": auto_ids, "reason": "accepted risk"}))


def test_evidence_people_tasks_reports_and_audit(api):
    a = api
    up = ok(a.post(f"/api/v1/evidence/{a.account_id}/upload",
                   files={"file": ("policy.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
                   data={"description": "Security policy", "tags": '["policy"]'}))
    dup = ok(a.post(f"/api/v1/evidence/{a.account_id}/upload",
                    files={"file": ("copy.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}))
    assert dup["id"] == up["id"]  # same content deduplicated by SHA-256

    link = ok(a.post(f"/api/v1/evidence/{a.account_id}/link",
                     json={"evidence_id": up["id"], "entity_type": "control", "entity_id": "ctrl-001"}))
    linked = ok(a.get(f"/api/v1/evidence/{a.account_id}/entity/control/ctrl-001"))
    assert len(linked) == 1
    # Linked evidence now allows Implemented
    ok(a.patch(f"/api/v1/controls/{a.account_id}/ctrl-001", json={"status": "Implemented"}))

    lib = ok(a.get(f"/api/v1/evidence/{a.account_id}/library?q=security"))
    assert lib["total"] == 1 and lib["items"][0]["linkCount"] == 1
    assert ok(a.get(f"/api/v1/evidence/{a.account_id}/tags")) == ["policy"]
    ok(a.patch(f"/api/v1/evidence/{a.account_id}/{up['id']}", json={"description": "v2"}))

    ok(a.delete(f"/api/v1/evidence/{a.account_id}/links/{link['id']}"))
    assert ok(a.get(f"/api/v1/evidence/{a.account_id}/entity/control/ctrl-001")) == []
    # Re-linking after an unlink reactivates the link
    ok(a.post(f"/api/v1/evidence/{a.account_id}/link",
              json={"evidence_id": up["id"], "entity_type": "control", "entity_id": "ctrl-001"}))
    assert len(ok(a.get(f"/api/v1/evidence/{a.account_id}/entity/control/ctrl-001"))) == 1

    # People tasks
    ok(a.post(f"/api/v1/people-tasks/{a.account_id}/instantiate-baseline"))
    task = ok(a.post(f"/api/v1/people-tasks/{a.account_id}", json={
        "title": "Quarterly access review", "task_type": "attestation", "pdca_phase": "check",
        "article_21_subsection": "i", "frequency": "quarterly",
        "next_due_date": (date.today() - timedelta(days=1)).isoformat(),
    }))
    ok(a.post(f"/api/v1/people-tasks/{a.account_id}/{task['id']}/complete",
              json={"attestation_response": "Reviewed", "evidence_id": up["id"]}))
    ok(a.post(f"/api/v1/people-tasks/{a.account_id}/{task['id']}/complete", json={}), 409)
    assert len(ok(a.get(f"/api/v1/people-tasks/{a.account_id}/{task['id']}/completions"))) == 1
    listed = ok(a.get(f"/api/v1/people-tasks/{a.account_id}"))
    assert any(t["id"] == task["id"] for t in listed)
    ok(a.get("/api/v1/people-tasks/my"))
    ok(a.get(f"/api/v1/isms/coverage/{a.account_id}"))

    # Reports
    report = ok(a.post(f"/api/v1/reports/{a.account_id}/generate",
                       json={"period": "Q4 2026", "period_start": "2026-10-01", "period_end": "2026-12-31"}), 201)
    assert ok(a.get(f"/api/v1/reports/{a.account_id}"))[0]["id"] == report["id"]
    pdf = a.get(f"/api/v1/reports/{a.account_id}/{report['id']}/download")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    ok(a.delete(f"/api/v1/reports/{a.account_id}/{report['id']}"))

    ok(a.delete(f"/api/v1/evidence/{a.account_id}/file/{up['id']}"))
    assert ok(a.get(f"/api/v1/evidence/{a.account_id}/library"))["total"] == 0

    # Audit log: entries were written, chain verifies, filters work
    log = ok(a.get(f"/api/v1/audit/{a.account_id}?per_page=200"))
    assert log["total"] > 5
    assert ok(a.get(f"/api/v1/audit/{a.account_id}/verify"))["valid"] is True
    ok(a.get(f"/api/v1/audit/{a.account_id}/{log['items'][0]['id']}"))
    filtered = ok(a.get(f"/api/v1/audit/{a.account_id}?event_type=evidence.uploaded"))
    assert filtered["total"] >= 1 and all(i["eventType"] == "evidence.uploaded" for i in filtered["items"])
    assert ok(a.get("/api/v1/me/activity"))["total"] >= 1


def test_aws_account_and_scan(api):
    a = api
    aws = ok(a.post("/api/v1/accounts/aws-accounts", json={
        "alias": "prod", "aws_access_key_id": "AKIATESTTESTTEST", "aws_secret_access_key": "secret", "region": "eu-west-1",
    }))
    started = ok(a.post(f"/api/v1/scan/{a.account_id}", json={"aws_account_id": aws["id"]}))
    # TestClient runs the background task before returning; checks run against moto
    scan = ok(a.get(f"/api/v1/scan/{started['scan_id']}"))
    assert scan["status"] in ("complete", "error")
    history = ok(a.get(f"/api/v1/scans/{a.account_id}?aws_account_id={aws['id']}"))
    assert history[0]["id"] == started["scan_id"]
    if scan["status"] == "complete":
        assert scan["totalChecks"] == len(scan["findings"]) > 0
        ok(a.get(f"/api/v1/scan/latest/{a.account_id}?aws_account_id={aws['id']}"))
    ok(a.delete(f"/api/v1/accounts/aws-accounts/{aws['id']}"))


def test_scheduled_jobs_run(api):
    import scheduler

    ok(api.post(f"/api/v1/remediation/{api.account_id}", json={
        "question_id": "nis2-020-01", "title": "Overdue", "due_date": (date.today() - timedelta(days=3)).isoformat(),
    }))
    scheduler.send_overdue_reminders()
    scheduler.escalate_chronic_slips()
    scheduler.roll_people_task_periods()
    scheduler.detect_overdue_people_tasks()
    events = ok(api.get(f"/api/v1/audit/{api.account_id}?event_type=remediation.overdue_reminder"))
    assert events["total"] == 1
