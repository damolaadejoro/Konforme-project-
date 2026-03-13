"""AWS cloud provider implementation wrapping existing scanner checks."""

import logging

from scanner.base import CheckResult, CloudProviderType
from scanner.provider import CloudProvider
from scanner.runner import create_session, run_all_checks

logger = logging.getLogger("konforme.scanner.aws")


class AWSProvider(CloudProvider):
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
