"""Report PDF storage — filesystem with S3 support."""

import hashlib
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from config import settings

REPORT_STORAGE_PATH = os.getenv(
    "REPORT_STORAGE_PATH",
    str(Path(__file__).parent / "storage" / "reports"),
)


def _use_s3() -> bool:
    return bool(settings.s3_reports_bucket)


def _s3_client():
    kwargs = {"region_name": settings.s3_reports_region}
    # Use IAM role credentials (EC2 instance profile) by default.
    # Only set explicit keys if evidence keys are configured (shared creds).
    if settings.s3_evidence_access_key_id:
        kwargs["aws_access_key_id"] = settings.s3_evidence_access_key_id
        kwargs["aws_secret_access_key"] = settings.s3_evidence_secret_access_key
    return boto3.client("s3", **kwargs)


def _s3_key(relative_path: str) -> str:
    return f"{settings.s3_reports_prefix}{relative_path}"


def store_pdf(account_id: str, report_id: str, pdf_bytes: bytes) -> tuple[str, int, str]:
    """Persist a generated PDF. Returns (relative_path, size_bytes, sha256_hex)."""
    size = len(pdf_bytes)
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    relative = f"{account_id}/{report_id}.pdf"

    if _use_s3():
        client = _s3_client()
        client.put_object(
            Bucket=settings.s3_reports_bucket,
            Key=_s3_key(relative),
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    else:
        account_dir = Path(REPORT_STORAGE_PATH) / account_id
        account_dir.mkdir(parents=True, exist_ok=True)
        file_path = account_dir / f"{report_id}.pdf"
        file_path.write_bytes(pdf_bytes)

    return relative, size, sha


def load_pdf(file_path: str) -> bytes:
    """Load a stored PDF."""
    if _use_s3():
        client = _s3_client()
        try:
            resp = client.get_object(
                Bucket=settings.s3_reports_bucket,
                Key=_s3_key(file_path),
            )
            return resp["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"PDF not found: {file_path}")
            raise
    else:
        full = (Path(REPORT_STORAGE_PATH) / file_path).resolve()
        base = Path(REPORT_STORAGE_PATH).resolve()
        if not str(full).startswith(str(base)):
            raise ValueError("Path traversal attempt blocked")
        if not full.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        return full.read_bytes()


def delete_pdf(file_path: str) -> None:
    """Delete a stored PDF file."""
    if _use_s3():
        client = _s3_client()
        try:
            client.delete_object(
                Bucket=settings.s3_reports_bucket,
                Key=_s3_key(file_path),
            )
        except ClientError:
            pass
    else:
        full = (Path(REPORT_STORAGE_PATH) / file_path).resolve()
        base = Path(REPORT_STORAGE_PATH).resolve()
        if str(full).startswith(str(base)) and full.exists():
            full.unlink()
