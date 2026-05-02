"""Cloud credentials management API — multi-provider support."""

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account
from database import get_db
from encryption import decrypt_value, encrypt_value
from models import Account, CloudCredential, OAuthState
from schemas import (
    AddAwsAccountRequest,
    AddAwsRoleRequest,
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
    conn_type = None
    if cred.provider == "aws":
        conn_type = getattr(cred, "aws_connection_type", None) or "keys"
    elif cred.provider == "azure":
        conn_type = getattr(cred, "azure_connection_type", None) or "client_secret"

    resp = CloudCredentialResponse(
        id=cred.id,
        provider=cred.provider,
        alias=cred.alias,
        is_active=cred.is_active,
        added_at=cred.added_at,
        connection_type=conn_type,
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
    # Clear encrypted credential fields on removal
    cred.aws_access_key_id = None
    cred.aws_secret_access_key = None
    cred.aws_session_token = None
    cred.aws_external_id = None
    cred.aws_role_arn = None
    cred.azure_tenant_id = None
    cred.azure_client_id = None
    cred.azure_client_secret = None
    cred.azure_subscription_id = None
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

    if cred.provider == "azure" and getattr(cred, "azure_connection_type", "client_secret") == "oauth":
        from scanner.azure_oauth_provider import AzureOAuthProvider
        provider = AzureOAuthProvider(
            tenant_id=decrypt_value(cred.azure_tenant_id),
            subscription_id=decrypt_value(cred.azure_subscription_id),
        )
    elif cred.provider == "azure":
        from scanner.azure_provider import AzureProvider
        provider = AzureProvider(
            tenant_id=decrypt_value(cred.azure_tenant_id),
            client_id=decrypt_value(cred.azure_client_id),
            client_secret=decrypt_value(cred.azure_client_secret),
            subscription_id=decrypt_value(cred.azure_subscription_id),
        )
    elif cred.provider == "aws" and getattr(cred, "aws_connection_type", "keys") == "role":
        from scanner.aws_provider import AWSRoleProvider
        provider = AWSRoleProvider(
            role_arn=cred.aws_role_arn,
            external_id=decrypt_value(cred.aws_external_id),
            region=cred.aws_region or "eu-west-1",
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


# ---------------------------------------------------------------------------
# AWS CloudFormation Role Assumption Flow
# ---------------------------------------------------------------------------


@router.get("/cloud-credentials/{account_id}/aws/initiate")
def initiate_aws_role_connection(
    account_id: str,
    alias: str = Query(..., description="Friendly name for this AWS connection"),
    region: str = Query("eu-west-1", description="AWS region"),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Generate an external ID and CloudFormation quick-create URL."""
    enforce_account_access(account, account_id)

    external_id = secrets.token_urlsafe(32)

    cred = CloudCredential(
        account_id=account_id,
        provider="aws",
        alias=alias,
        aws_connection_type="role",
        aws_external_id=encrypt_value(external_id),
        aws_region=region,
        is_active=False,  # pending until role ARN confirmed
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)

    cf_template_url = os.environ.get(
        "CF_TEMPLATE_URL",
        "https://konforme-public-assets.s3.eu-west-1.amazonaws.com/cf-templates/konforme-audit-role.yaml",
    )
    konforme_account_id = os.environ.get("KONFORME_AWS_ACCOUNT_ID", "859217211781")

    cf_params = urlencode({
        "templateURL": cf_template_url,
        "stackName": "KonformeAuditRole",
        "param_ExternalId": external_id,
        "param_TrustedAccountId": konforme_account_id,
    })
    cf_url = f"https://console.aws.amazon.com/cloudformation/home?region={region}#/stacks/quickcreate?{cf_params}"

    return {
        "credential_id": cred.id,
        "external_id": external_id,
        "cf_url": cf_url,
    }


@router.post("/cloud-credentials/{account_id}/aws/role", response_model=CloudCredentialResponse)
def complete_aws_role_connection(
    account_id: str,
    req: AddAwsRoleRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Validate the IAM role and activate the credential."""
    enforce_account_access(account, account_id)

    cred = (
        db.query(CloudCredential)
        .filter(
            CloudCredential.id == req.credential_id,
            CloudCredential.account_id == account_id,
            CloudCredential.aws_connection_type == "role",
            CloudCredential.is_active == False,
        )
        .first()
    )
    if not cred:
        raise HTTPException(status_code=404, detail="Pending AWS role credential not found")

    external_id = decrypt_value(cred.aws_external_id)
    aws_account_id = _validate_role_arn(req.role_arn, external_id)

    # Duplicate check
    existing = (
        db.query(CloudCredential)
        .filter(
            CloudCredential.account_id == account_id,
            CloudCredential.aws_role_arn == req.role_arn,
            CloudCredential.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="This IAM role is already connected")

    cred.aws_role_arn = req.role_arn
    cred.aws_account_id = aws_account_id
    cred.aws_region = req.region
    cred.is_active = True
    db.commit()
    db.refresh(cred)
    return _credential_to_response(cred)


def _validate_role_arn(role_arn: str, external_id: str) -> str:
    """Assume the role and return the target AWS account ID, or raise 400."""
    import boto3
    from botocore.exceptions import ClientError

    try:
        sts = boto3.client("sts")
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="KonformeValidation",
            ExternalId=external_id,
            DurationSeconds=900,
        )
        assumed_arn = response["AssumedRoleUser"]["Arn"]
        return assumed_arn.split(":")[4]
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("AccessDenied", "InvalidClientTokenId", "AccessDeniedException"):
            raise HTTPException(
                status_code=400,
                detail="Could not assume the IAM role. Verify the Role ARN and that the CloudFormation stack deployed successfully.",
            )
        import logging
        logging.getLogger(__name__).error("AWS STS error: %s", e.response["Error"]["Message"])
        raise HTTPException(status_code=400, detail="AWS connection failed. Please check your credentials and try again.")


# ---------------------------------------------------------------------------
# Azure Admin Consent OAuth Flow
# ---------------------------------------------------------------------------


@router.get("/cloud-credentials/{account_id}/azure/oauth/initiate")
def initiate_azure_oauth(
    account_id: str,
    alias: str = Query(...),
    subscription_id: str = Query(...),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Start the Azure admin consent flow."""
    azure_client_id = os.environ.get("AZURE_APP_CLIENT_ID", "")
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    if not azure_client_id:
        raise HTTPException(status_code=500, detail="Azure OAuth not configured")

    enforce_account_access(account, account_id)

    state = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    oauth_state = OAuthState(
        account_id=account_id,
        state_token=state,
        provider="azure",
        alias=alias,
        subscription_id=subscription_id,
        expires_at=expires,
    )
    db.add(oauth_state)
    db.commit()

    redirect_uri = f"{api_base_url}/api/v1/cloud-credentials/azure/callback"

    params = urlencode({
        "client_id": azure_client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    })
    auth_url = f"https://login.microsoftonline.com/common/adminconsent?{params}"

    return {"auth_url": auth_url, "state": state}


@router.get("/cloud-credentials/azure/callback")
def azure_oauth_callback(
    tenant: str = Query(None),
    admin_consent: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: Session = Depends(get_db),
):
    """Handle the Azure admin consent redirect callback."""
    frontend_url = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5173")

    if error:
        return RedirectResponse(
            url=f"{frontend_url}/settings?azure_error={error_description or error}"
        )

    if not state:
        return RedirectResponse(url=f"{frontend_url}/settings?azure_error=missing_state")

    # Validate state
    oauth_state = (
        db.query(OAuthState)
        .filter(
            OAuthState.state_token == state,
            OAuthState.provider == "azure",
            OAuthState.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not oauth_state:
        return RedirectResponse(url=f"{frontend_url}/settings?azure_error=invalid_or_expired_state")

    tenant_id = tenant
    if not tenant_id or admin_consent != "True":
        db.delete(oauth_state)
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/settings?azure_error=consent_denied")

    # Validate the consent works by getting an access token via client credentials
    azure_client_id = os.environ.get("AZURE_APP_CLIENT_ID", "")
    azure_client_secret = os.environ.get("AZURE_APP_CLIENT_SECRET", "")
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    try:
        token_resp = httpx.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": azure_client_id,
                "client_secret": azure_client_secret,
                "scope": "https://management.azure.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        if token_resp.status_code != 200:
            db.delete(oauth_state)
            db.commit()
            return RedirectResponse(
                url=f"{frontend_url}/settings?azure_error=token_validation_failed"
            )
    except Exception:
        db.delete(oauth_state)
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/settings?azure_error=token_validation_failed")

    # Create the credential
    cred = CloudCredential(
        account_id=oauth_state.account_id,
        provider="azure",
        alias=oauth_state.alias,
        azure_connection_type="oauth",
        azure_tenant_id=encrypt_value(tenant_id),
        azure_subscription_id=encrypt_value(oauth_state.subscription_id),
        is_active=True,
    )
    db.add(cred)
    db.delete(oauth_state)
    db.commit()
    db.refresh(cred)

    return RedirectResponse(
        url=f"{frontend_url}/settings?azure_connected=1&credential_id={cred.id}"
    )
