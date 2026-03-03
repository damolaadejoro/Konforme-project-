import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from audit import log_scan_complete, log_scan_error, log_scan_start
from auth import enforce_account_access, get_current_account
from encryption import decrypt_value
from database import SessionLocal, get_db
from models import Account, AwsAccount, Scan, ScanResult
from scanner.nis2_mapping import NIS2_MAPPING
from scanner.runner import run_all_checks
from schemas import (
    DomainScoreResponse,
    FindingResponse,
    ScanResponse,
    ScanStartRequest,
    ScanStartResponse,
)

router = APIRouter()

SEVERITY_WEIGHTS = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _calculate_technical_score(results: list[ScanResult]) -> float:
    total_weight = 0.0
    pass_weight = 0.0
    for r in results:
        if r.status in ("warn", "info"):
            continue
        w = SEVERITY_WEIGHTS.get(r.severity, 1)
        total_weight += w
        if r.status == "pass":
            pass_weight += w
    if total_weight == 0:
        return 0.0
    return round((pass_weight / total_weight) * 100, 1)


def _build_domain_scores(results: list[ScanResult]) -> list[dict]:
    domains: dict[str, dict] = {}
    for r in results:
        if r.status in ("warn", "info"):
            continue
        mapping = NIS2_MAPPING.get(r.check_id, {})
        domain = mapping.get("domain", "Other")
        article = mapping.get("article", "")
        if domain not in domains:
            domains[domain] = {"domain": domain, "article": article, "passed": 0, "failed": 0, "total": 0}
        domains[domain]["total"] += 1
        if r.status == "pass":
            domains[domain]["passed"] += 1
        else:
            domains[domain]["failed"] += 1
    result = []
    for d in domains.values():
        score = round((d["passed"] / d["total"]) * 100, 1) if d["total"] > 0 else 0.0
        result.append({**d, "score": score})
    return result


def execute_scan(
    scan_id: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    region: str,
    account_id: str,
    account_name: str,
):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return
        scan.status = "running"
        db.commit()
        log_scan_start(scan_id, account_id)

        check_results = run_all_checks(access_key_id, secret_access_key, session_token, region)

        critical = high = medium = low = passed = failed = 0
        for cr in check_results:
            sr = ScanResult(
                id=str(uuid.uuid4()),
                scan_id=scan_id,
                check_id=cr.check_id,
                nis2_article=cr.nis2_article,
                nis2_requirement=cr.nis2_requirement,
                status=cr.status,
                severity=cr.severity,
                title=cr.title,
                message=cr.message,
                remediation=cr.remediation,
                remediation_steps=json.dumps(cr.remediation_steps) if cr.remediation_steps else "",
                resource=cr.resource,
            )
            db.add(sr)
            if cr.status == "pass":
                passed += 1
            elif cr.status == "fail":
                failed += 1
                if cr.severity == "critical":
                    critical += 1
                elif cr.severity == "high":
                    high += 1
                elif cr.severity == "medium":
                    medium += 1
                elif cr.severity == "low":
                    low += 1

        db.flush()
        all_results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
        score = _calculate_technical_score(all_results)

        scan.status = "complete"
        scan.completed_at = datetime.now(timezone.utc)
        scan.overall_score = score
        scan.total_checks = len(check_results)
        scan.passed = passed
        scan.failed = failed
        scan.critical_count = critical
        scan.high_count = high
        scan.medium_count = medium
        scan.low_count = low
        db.commit()
        log_scan_complete(scan_id, account_id, score)
    except Exception as e:
        db.rollback()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = "error"
            db.commit()
        log_scan_error(scan_id, account_id, str(e))
    finally:
        db.close()


@router.post("/scan/{account_id}", response_model=ScanStartResponse)
def start_scan(
    account_id: str,
    req: ScanStartRequest,
    background_tasks: BackgroundTasks,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Look up the AWS account and verify ownership
    aws_acc = db.query(AwsAccount).filter(
        AwsAccount.id == req.aws_account_id,
        AwsAccount.account_id == account_id,
        AwsAccount.is_active == True,
    ).first()
    if not aws_acc:
        raise HTTPException(status_code=404, detail="AWS account not found or inactive")

    # Check for already running scan on this AWS account
    running = db.query(Scan).filter(
        Scan.account_id == account_id,
        Scan.aws_account_id == req.aws_account_id,
        Scan.status.in_(["queued", "running"]),
    ).first()
    if running:
        raise HTTPException(
            status_code=409,
            detail="Scan already in progress for this AWS account",
            headers={"X-Scan-Id": running.id},
        )

    scan = Scan(account_id=account_id, aws_account_id=aws_acc.id)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(
        execute_scan,
        scan.id,
        decrypt_value(aws_acc.aws_access_key_id),
        decrypt_value(aws_acc.aws_secret_access_key),
        decrypt_value(aws_acc.aws_session_token) if aws_acc.aws_session_token else None,
        aws_acc.aws_region,
        account.id,
        account.name,
    )

    return ScanStartResponse(scan_id=scan.id, status="queued")


@router.get("/scan/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    enforce_account_access(account, scan.account_id)

    # Get the AWS account info if available
    aws_acc = scan.aws_account
    region = aws_acc.aws_region if aws_acc else "unknown"
    aws_account_id_str = aws_acc.aws_account_id if aws_acc else ""

    results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
    domain_scores = _build_domain_scores(results)

    findings = []
    for r in results:
        mapping = NIS2_MAPPING.get(r.check_id, {})
        findings.append(
            FindingResponse(
                id=r.id,
                checkName=r.check_id,
                description=r.message,
                resource=r.resource,
                resourceType=mapping.get("domain", "AWS"),
                severity=r.severity,
                status="review" if r.status == "warn" else "info" if r.status == "info" else r.status,
                article=r.nis2_article,
                articleTitle=mapping.get("article_title", ""),
                region=region,
                evidence=r.message,
                remediation=r.remediation,
                remediationSteps=json.loads(r.remediation_steps) if r.remediation_steps else [],
                domain=mapping.get("domain", "Other"),
                timestamp=scan.started_at.isoformat() if scan.started_at else "",
            )
        )

    return ScanResponse(
        id=scan.id,
        accountName=account.name,
        accountId=aws_account_id_str,
        awsAccountId=aws_acc.id if aws_acc else None,
        awsAlias=aws_acc.alias if aws_acc else None,
        region=region,
        startedAt=scan.started_at.isoformat() if scan.started_at else "",
        completedAt=scan.completed_at.isoformat() if scan.completed_at else None,
        status=scan.status,
        overallScore=scan.overall_score,
        totalChecks=scan.total_checks,
        passed=scan.passed,
        failed=scan.failed,
        criticalCount=scan.critical_count,
        highCount=scan.high_count,
        mediumCount=scan.medium_count,
        lowCount=scan.low_count,
        findings=findings,
        domainScores=[DomainScoreResponse(**d) for d in domain_scores],
    )
