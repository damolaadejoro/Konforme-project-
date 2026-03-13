"""Cloud credentials management API — multi-provider support."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account
from database import get_db
from encryption import decrypt_value, encrypt_value
from models import Account, CloudCredential
from schemas import (
    AddAwsAccountRequest,
    AddAzureCredentialRequest,
    CloudCredentialListResponse,
    CloudCredentialResponse,
)

router = APIRouter()


def _mask(value: str | None, show_last: int = 4) -> str | None:
    if not value:
        return None
    if len(value) <= show_last:
        return "****"
    return "****" + value[-show_last:]


def _credential_to_response(cred: CloudCredential) -> CloudCredentialResponse:
    resp = CloudCredentialResponse(
        id=cred.id,
        provider=cred.provider,
        alias=cred.alias,
        is_active=cred.is_active,
        added_at=cred.added_at,
    )
    if cred.provider == "aws":
        resp.aws_account_id = cred.aws_account_id
        resp.aws_region = cred.aws_region
    elif cred.provider == "azure":
        resp.azure_subscription_id = _mask(
            decrypt_value(cred.azure_subscription_id) if cred.azure_subscription_id else None
        )
        resp.azure_tenant_id = _mask(
            decrypt_value(cred.azure_tenant_id) if cred.azure_tenant_id else None
        )
    return resp


@router.get("/cloud-credentials/{account_id}", response_model=CloudCredentialListResponse)
def list_cloud_credentials(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    creds = (
        db.query(CloudCredential)
        .filter(CloudCredential.account_id == account_id, CloudCredential.is_active == True)
        .all()
    )
    return CloudCredentialListResponse(
        credentials=[_credential_to_response(c) for c in creds]
    )


@router.post("/cloud-credentials/{account_id}/azure", response_model=CloudCredentialResponse)
def add_azure_credential(
    account_id: str,
    req: AddAzureCredentialRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Validate credentials by attempting to get a token
    from scanner.azure_provider import AzureProvider
    provider = AzureProvider(
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
        subscription_id=req.subscription_id,
    )
    if not provider.validate_credentials():
        raise HTTPException(
            status_code=400,
            detail="Azure credential validation failed. Check tenant_id, client_id, client_secret, and subscription_id.",
        )

    cred = CloudCredential(
        account_id=account_id,
        provider="azure",
        alias=req.alias,
        azure_tenant_id=encrypt_value(req.tenant_id),
        azure_client_id=encrypt_value(req.client_id),
        azure_client_secret=encrypt_value(req.client_secret),
        azure_subscription_id=encrypt_value(req.subscription_id),
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return _credential_to_response(cred)


@router.delete("/cloud-credentials/{account_id}/{credential_id}")
def remove_cloud_credential(
    account_id: str,
    credential_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    cred = (
        db.query(CloudCredential)
        .filter(
            CloudCredential.id == credential_id,
            CloudCredential.account_id == account_id,
        )
        .first()
    )
    if not cred:
        raise HTTPException(status_code=404, detail="Cloud credential not found")
    cred.is_active = False
    db.commit()
    return {"status": "removed"}


@router.post("/cloud-credentials/{account_id}/{credential_id}/validate")
def validate_cloud_credential(
    account_id: str,
    credential_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    cred = (
        db.query(CloudCredential)
        .filter(
            CloudCredential.id == credential_id,
            CloudCredential.account_id == account_id,
            CloudCredential.is_active == True,
        )
        .first()
    )
    if not cred:
        raise HTTPException(status_code=404, detail="Cloud credential not found")

    if cred.provider == "azure":
        from scanner.azure_provider import AzureProvider
        provider = AzureProvider(
            tenant_id=decrypt_value(cred.azure_tenant_id),
            client_id=decrypt_value(cred.azure_client_id),
            client_secret=decrypt_value(cred.azure_client_secret),
            subscription_id=decrypt_value(cred.azure_subscription_id),
        )
    elif cred.provider == "aws":
        from scanner.aws_provider import AWSProvider
        provider = AWSProvider(
            access_key_id=decrypt_value(cred.aws_access_key_id),
            secret_access_key=decrypt_value(cred.aws_secret_access_key),
            session_token=decrypt_value(cred.aws_session_token) if cred.aws_session_token else None,
            region=cred.aws_region or "eu-west-1",
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {cred.provider}")

    valid = provider.validate_credentials()
    return {"valid": valid, "provider": cred.provider}
