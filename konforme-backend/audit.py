import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("konforme.audit")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _log(event_type: str, **kwargs: object) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **kwargs,
    }
    logger.info(json.dumps(entry))


def log_auth_success(account_id: str) -> None:
    _log("auth_success", account_id=account_id)


def log_auth_failure(reason: str) -> None:
    _log("auth_failure", reason=reason)


def log_register(account_id: str, email: str) -> None:
    _log("register", account_id=account_id, email=email)


def log_login_failure(email: str) -> None:
    _log("login_failure", email=email)


def log_aws_connect(account_id: str, aws_account_id: str, alias: str = "") -> None:
    _log("aws_connect", account_id=account_id, aws_account_id=aws_account_id, alias=alias)


def log_aws_account_added(account_id: str, aws_account_id: str, alias: str) -> None:
    _log("aws_account_added", account_id=account_id, aws_account_id=aws_account_id, alias=alias)


def log_aws_account_removed(account_id: str, aws_account_id: str, alias: str) -> None:
    _log("aws_account_removed", account_id=account_id, aws_account_id=aws_account_id, alias=alias)


def log_scan_start(scan_id: str, account_id: str) -> None:
    _log("scan_start", scan_id=scan_id, account_id=account_id)


def log_scan_complete(scan_id: str, account_id: str, score: float | None) -> None:
    _log("scan_complete", scan_id=scan_id, account_id=account_id, score=score)


def log_scan_error(scan_id: str, account_id: str, error: str) -> None:
    _log("scan_error", scan_id=scan_id, account_id=account_id, error=error)


def log_access_violation(account_id: str, resource_id: str) -> None:
    _log("access_violation", account_id=account_id, attempted_resource=resource_id)
