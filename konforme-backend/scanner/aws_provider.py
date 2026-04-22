"""AWS cloud provider implementation wrapping existing scanner checks."""

import logging

import boto3

from scanner.base import CheckResult, CloudProviderType
from scanner.provider import CloudProvider
from scanner.runner import create_session, run_all_checks, run_all_checks_with_session

logger = logging.getLogger("konforme.scanner.aws")


class AWSProvider(CloudProvider):
    """AWS provider using long-lived access keys (legacy)."""

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str | None = None,
        region: str = "eu-west-1",
    ):
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._session_token = session_token
        self._region = region

    @property
    def provider_type(self) -> CloudProviderType:
        return CloudProviderType.AWS

    @property
    def display_name(self) -> str:
        return "Amazon Web Services"

    def run_all_checks(self) -> list[CheckResult]:
        return run_all_checks(
            self._access_key_id,
            self._secret_access_key,
            self._session_token,
            self._region,
        )

    def validate_credentials(self) -> bool:
        try:
            session = create_session(
                self._access_key_id,
                self._secret_access_key,
                self._session_token,
                self._region,
            )
            sts = session.client("sts")
            sts.get_caller_identity()
            return True
        except Exception as e:
            logger.warning("AWS credential validation failed: %s", e)
            return False


class AWSRoleProvider(CloudProvider):
    """AWS provider using cross-account IAM role assumption (no stored keys)."""

    def __init__(self, role_arn: str, external_id: str, region: str = "eu-west-1"):
        self._role_arn = role_arn
        self._external_id = external_id
        self._region = region

    def _assume_role(self) -> boto3.Session:
        sts = boto3.client("sts")
        response = sts.assume_role(
            RoleArn=self._role_arn,
            RoleSessionName="KonformeScan",
            ExternalId=self._external_id,
            DurationSeconds=3600,
        )
        creds = response["Credentials"]
        return boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=self._region,
        )

    @property
    def provider_type(self) -> CloudProviderType:
        return CloudProviderType.AWS

    @property
    def display_name(self) -> str:
        return "Amazon Web Services (IAM Role)"

    def run_all_checks(self) -> list[CheckResult]:
        session = self._assume_role()
        return run_all_checks_with_session(session)

    def validate_credentials(self) -> bool:
        try:
            self._assume_role()
            return True
        except Exception as e:
            logger.warning("AWS role assumption failed: %s", e)
            return False
