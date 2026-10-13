import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException

from audit import log_aws_account_added, log_aws_account_removed
from auth import get_current_account
from encryption import encrypt_value
from database import Session, get_db
from models import Account, AwsAccount
from eu_countries import VALID_EU_CODES
from schemas import (
    AccountResponse,
    AccountUpdateRequest,
    AddAwsAccountRequest,
    AwsAccountResponse,
)

router = APIRouter()


def _validate_aws_creds(access_key: str, secret_key: str, session_token: str | None, region: str) -> str:
    """Validate AWS credentials via STS and return the AWS account ID."""
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name=region,
        )
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        return identity["Account"]
    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid AWS credentials. Please verify your access key, secret key, and region.",
        )


def _aws_account_to_response(aws_acc: AwsAccount) -> AwsAccountResponse:
    return AwsAccountResponse(
        id=aws_acc.id,
        alias=aws_acc.alias,
        aws_account_id=aws_acc.aws_account_id,
        aws_region=aws_acc.aws_region,
        is_active=aws_acc.is_active,
        added_at=aws_acc.added_at,
    )


@router.get("/accounts", response_model=AccountResponse)
def get_account(account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    active_aws = [a for a in account.aws_accounts if a.is_active]
    return AccountResponse(
        id=account.id,
        name=account.name,
        is_active=account.is_active,
        country=account.country,
        language=account.language,
        connected_at=account.connected_at,
        aws_accounts=[_aws_account_to_response(a) for a in active_aws],
    )


@router.put("/accounts")
def update_account(
    req: AccountUpdateRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if req.name is not None:
        account.name = req.name
    if req.email is not None:
        existing = db.lookup(Account, "email", req.email)
        if existing and existing.id != account.id:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        account.email = req.email
    if req.country is not None:
        if req.country != "" and req.country not in VALID_EU_CODES:
            raise HTTPException(status_code=422, detail=f"Invalid EU country code: {req.country}")
        account.country = req.country if req.country != "" else None
    if req.language is not None:
        if req.language not in ("en", "pt", "de", "fr", "es", "it", "nl"):
            raise HTTPException(status_code=422, detail=f"Unsupported language: {req.language}")
        account.language = req.language
    db.commit()
    db.refresh(account)
    return {"account_id": account.id, "account_name": account.name, "email": account.email}


@router.post("/accounts/aws-accounts", response_model=AwsAccountResponse)
def add_aws_account(
    req: AddAwsAccountRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    aws_account_id = _validate_aws_creds(
        req.aws_access_key_id, req.aws_secret_access_key, req.aws_session_token, req.region
    )

    # Prevent duplicate: same AWS account ID already linked to this Konforme account
    existing = next(
        (a for a in db.list(AwsAccount, account.id) if a.aws_account_id == aws_account_id and a.is_active),
        None,
    )
    if existing:
        raise HTTPException(status_code=409, detail="This AWS account is already connected")

    aws_acc = AwsAccount(
        account_id=account.id,
        alias=req.alias,
        aws_access_key_id=encrypt_value(req.aws_access_key_id),
        aws_secret_access_key=encrypt_value(req.aws_secret_access_key),
        aws_session_token=encrypt_value(req.aws_session_token) if req.aws_session_token else None,
        aws_region=req.region,
        aws_account_id=aws_account_id,
    )
    db.add(aws_acc)
    db.commit()
    db.refresh(aws_acc)

    log_aws_account_added(account.id, aws_account_id, req.alias)

    return _aws_account_to_response(aws_acc)


@router.delete("/accounts/aws-accounts/{aws_account_id}")
def remove_aws_account(
    aws_account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    aws_acc = db.get_by_key(AwsAccount, account.id, id=aws_account_id)
    if not aws_acc:
        raise HTTPException(status_code=404, detail="AWS account not found")

    aws_acc.is_active = False
    # Clear encrypted credential fields on removal
    aws_acc.aws_access_key_id = None
    aws_acc.aws_secret_access_key = None
    aws_acc.aws_session_token = None
    db.commit()

    log_aws_account_removed(account.id, aws_acc.aws_account_id, aws_acc.alias)

    return {"detail": "AWS account deactivated"}
