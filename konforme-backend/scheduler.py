"""Daily scheduler for overdue reminders and chronic slip escalation."""

import logging
from datetime import date, timezone, datetime

from apscheduler.schedulers.background import BackgroundScheduler

from database import SessionLocal
from models import PeopleTask, RemediationTask, User, Account
import audit_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _get_account_admins(db, account_id: str) -> list[str]:
    """Return emails of owner/admin users for an account."""
    users = db.query(User).filter(
        User.account_id == account_id,
        User.is_active.is_(True),
        User.role.in_(["owner", "admin"]),
    ).all()
    return [u.email for u in users if u.email]


def send_overdue_reminders():
    """Send reminder emails for overdue remediation tasks."""
    from email_service import send_remediation_reminder
    from config import settings

    logger.info("Running overdue reminders job")
    db = SessionLocal()
    try:
        today = date.today()
        overdue_tasks = db.query(RemediationTask).filter(
            RemediationTask.status.in_(["open", "in_progress"]),
            RemediationTask.due_date < today,
        ).all()

        if not overdue_tasks:
            return

        # Group by account_id + assigned_to
        grouped: dict[tuple[str, str], list[RemediationTask]] = {}
        for task in overdue_tasks:
            key = (task.account_id, task.assigned_to or "")
            grouped.setdefault(key, []).append(task)

        for (account_id, assignee), tasks in grouped.items():
            if not assignee:
                # Send to account admins if no assignee
                emails = _get_account_admins(db, account_id)
            else:
                emails = [assignee] if "@" in assignee else []

            # Get account language
            account = db.query(Account).filter(Account.id == account_id).first()
            lang = account.language if account and account.language else "en"

            for email in emails:
                for task in tasks:
                    try:
                        task_url = f"{settings.frontend_base_url}/remediation"
                        send_remediation_reminder(
                            email, task.title,
                            task.due_date.isoformat() if task.due_date else "",
                            task_url, lang,
                        )
                    except Exception:
                        logger.exception("Failed to send overdue reminder for task %s", task.id)

            # Audit log
            audit_service.emit(
                db, account_id, "remediation.overdue_reminder",
                entity_type="remediation_task",
                metadata={"task_count": len(tasks), "assignee": assignee},
            )

        db.commit()
    except Exception:
        logger.exception("Overdue reminders job failed")
        db.rollback()
    finally:
        db.close()


def escalate_chronic_slips():
    """Send escalation emails for tasks with chronic rescheduling."""
    from email_service import send_escalation_notification
    import remediation_service

    logger.info("Running chronic slip escalation job")
    db = SessionLocal()
    try:
        # Find tasks that have been rescheduled 3+ times
        candidates = db.query(RemediationTask).filter(
            RemediationTask.status.in_(["open", "in_progress"]),
            RemediationTask.reschedule_count >= 3,
        ).all()

        # Also check cumulative extension for tasks with fewer reschedules
        additional = db.query(RemediationTask).filter(
            RemediationTask.status.in_(["open", "in_progress"]),
            RemediationTask.reschedule_count >= 1,
            RemediationTask.reschedule_count < 3,
            RemediationTask.original_due_date.isnot(None),
        ).all()

        chronic_tasks = list(candidates)
        for task in additional:
            if remediation_service.is_chronic_slip(task) and task not in chronic_tasks:
                chronic_tasks.append(task)

        if not chronic_tasks:
            return

        # Group by account
        by_account: dict[str, list[RemediationTask]] = {}
        for task in chronic_tasks:
            by_account.setdefault(task.account_id, []).append(task)

        for account_id, tasks in by_account.items():
            admin_emails = _get_account_admins(db, account_id)
            account = db.query(Account).filter(Account.id == account_id).first()
            lang = account.language if account and account.language else "en"

            for email in admin_emails:
                for task in tasks:
                    try:
                        send_escalation_notification(
                            email, task.title,
                            task.reschedule_count or 0, lang,
                        )
                    except Exception:
                        logger.exception("Failed to send escalation for task %s", task.id)

            audit_service.emit(
                db, account_id, "remediation.chronic_slip_escalation",
                entity_type="remediation_task",
                metadata={"task_count": len(tasks)},
                is_material=True,
            )

        db.commit()
    except Exception:
        logger.exception("Chronic slip escalation job failed")
        db.rollback()
    finally:
        db.close()


def roll_people_task_periods():
    """Advance next_due_date for expired people tasks."""
    import people_tasks_service

    logger.info("Running people task period rollover job")
    db = SessionLocal()
    try:
        result = people_tasks_service.roll_period(db)
        if result["rolled"] > 0:
            db.commit()
            logger.info("Rolled %d people task periods", result["rolled"])
    except Exception:
        logger.exception("People task period rollover job failed")
        db.rollback()
    finally:
        db.close()


def detect_overdue_people_tasks():
    """Send reminders for overdue people tasks."""
    from email_service import send_remediation_reminder
    from config import settings

    logger.info("Running overdue people tasks detection job")
    db = SessionLocal()
    try:
        today = date.today()
        overdue = (
            db.query(PeopleTask)
            .filter(
                PeopleTask.active.is_(True),
                PeopleTask.next_due_date.isnot(None),
                PeopleTask.next_due_date < today,
            )
            .all()
        )

        if not overdue:
            return

        by_account: dict[str, list[PeopleTask]] = {}
        for task in overdue:
            by_account.setdefault(task.account_id, []).append(task)

        for account_id, tasks in by_account.items():
            admin_emails = _get_account_admins(db, account_id)
            account = db.query(Account).filter(Account.id == account_id).first()
            lang = account.language if account and account.language else "en"

            for email in admin_emails:
                for task in tasks:
                    try:
                        task_url = f"{settings.frontend_base_url}/people-tasks/continuous"
                        send_remediation_reminder(
                            email, task.title,
                            task.next_due_date.isoformat() if task.next_due_date else "",
                            task_url, lang,
                        )
                    except Exception:
                        logger.exception("Failed to send people task overdue reminder for %s", task.id)

            audit_service.emit(
                db, account_id, "people_tasks.overdue_detected",
                entity_type="people_task",
                metadata={"task_count": len(tasks)},
            )

        db.commit()
    except Exception:
        logger.exception("Overdue people tasks detection job failed")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler with daily jobs."""
    scheduler.add_job(send_overdue_reminders, "cron", hour=8, minute=0, id="overdue_reminders", replace_existing=True)
    scheduler.add_job(escalate_chronic_slips, "cron", hour=8, minute=15, id="chronic_slip_escalation", replace_existing=True)
    scheduler.add_job(roll_people_task_periods, "cron", hour=0, minute=5, id="roll_people_task_periods", replace_existing=True)
    scheduler.add_job(detect_overdue_people_tasks, "cron", hour=8, minute=30, id="detect_overdue_people_tasks", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started with 4 daily jobs")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
