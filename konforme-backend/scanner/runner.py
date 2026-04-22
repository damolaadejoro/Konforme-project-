import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3

from scanner.base import CheckResult
from scanner.checks import discover_checks

logger = logging.getLogger("konforme.scanner")

CHECK_TIMEOUT = 30  # seconds per check
MAX_WORKERS = 8


def create_session(
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    region: str = "eu-west-1",
) -> boto3.Session:
    return boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
        region_name=region,
    )


def run_all_checks_with_session(session: boto3.Session) -> list[CheckResult]:
    """Run all checks using a pre-built boto3 session."""
    checks = discover_checks()
    all_results: list[CheckResult] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check.safe_run, session): check
            for check in checks
        }
        for future in as_completed(futures, timeout=CHECK_TIMEOUT * len(checks)):
            check = futures[future]
            try:
                results = future.result(timeout=CHECK_TIMEOUT)
                all_results.extend(results)
            except Exception as e:
                logger.error("Check %s timed out or failed: %s", check.check_id, e)
                all_results.append(
                    CheckResult(
                        check_id=check.check_id,
                        title=f"{check.check_id} (timeout)",
                        status="warn",
                        severity=check.severity,
                        message=f"Check timed out after {CHECK_TIMEOUT}s: {e}",
                        nis2_article=check.nis2_article,
                        nis2_requirement=check.nis2_requirement,
                        resource="N/A",
                        domain=check.domain,
                        resource_type="AWS",
                    )
                )

    return all_results


def run_all_checks(
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    region: str = "eu-west-1",
) -> list[CheckResult]:
    session = create_session(access_key_id, secret_access_key, session_token, region)
    return run_all_checks_with_session(session)
