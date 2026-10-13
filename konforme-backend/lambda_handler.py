"""AWS Lambda entrypoints.

One container image serves three functions, selected by the image CMD:

- lambda_handler.api     — HTTP traffic from API Gateway (FastAPI via Mangum)
- lambda_handler.worker  — async work: cloud scans and the daily scheduled jobs
- lambda_handler.migrate — seed reference data (base controls, mappings); run once per deploy
"""

import logging

from mangum import Mangum

from main import app, bootstrap_database, check_production_settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)

check_production_settings()

# lifespan="off": startup work (migrations, scheduler) must not run on every cold start
api = Mangum(app, lifespan="off")


def _run_aws_scan(event: dict) -> None:
    from database import SessionLocal
    from encryption import decrypt_value
    from models import AwsAccount
    from routers.scans import execute_scan

    # Credentials are decrypted here rather than passed in the event, so they never
    # appear in the async invocation payload.
    with SessionLocal() as db:
        aws_acc = db.get_by_key(AwsAccount, event["account_id"], id=event["aws_account_id"])
        if not aws_acc:
            logger.error("AWS account %s not found for scan %s", event["aws_account_id"], event["scan_id"])
            return
        access_key_id = decrypt_value(aws_acc.aws_access_key_id)
        secret_access_key = decrypt_value(aws_acc.aws_secret_access_key)
        session_token = decrypt_value(aws_acc.aws_session_token) if aws_acc.aws_session_token else None
        region = aws_acc.aws_region

    execute_scan(
        event["scan_id"],
        access_key_id,
        secret_access_key,
        session_token,
        region,
        event["account_id"],
        event["account_name"],
    )


def _run_provider_scan(event: dict) -> None:
    from routers.scans import execute_provider_scan

    execute_provider_scan(
        event["scan_id"],
        event["credential_id"],
        event["provider"],
        event["account_id"],
        event["account_name"],
    )


def _run_scheduled_job(event: dict) -> None:
    import scheduler

    jobs = {
        "overdue_reminders": scheduler.send_overdue_reminders,
        "chronic_slip_escalation": scheduler.escalate_chronic_slips,
        "roll_people_task_periods": scheduler.roll_people_task_periods,
        "detect_overdue_people_tasks": scheduler.detect_overdue_people_tasks,
    }
    job = jobs.get(event.get("job"))
    if job is None:
        raise ValueError(f"Unknown scheduled job: {event.get('job')!r}")
    job()


TASKS = {
    "scan_aws": _run_aws_scan,
    "scan_provider": _run_provider_scan,
    "scheduled_job": _run_scheduled_job,
}


def worker(event, context):
    task = event.get("task")
    handler = TASKS.get(task)
    if handler is None:
        raise ValueError(f"Unknown worker task: {task!r}")
    logger.info("Running worker task %s", task)
    handler(event)
    return {"ok": True, "task": task}


def migrate(event, context):
    # Seeds/refreshes reference data (base controls, question mappings)
    bootstrap_database()
    return {"ok": True}
