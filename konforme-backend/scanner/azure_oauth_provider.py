"""Azure cloud provider using admin consent OAuth flow (no customer secrets)."""

import logging
import os
import time

import httpx
from azure.core.credentials import AccessToken

from scanner.base import CheckResult, CloudProviderType
from scanner.provider import CloudProvider
from scanner.azure_checks import discover_azure_checks

logger = logging.getLogger("konforme.scanner.azure_oauth")

CHECK_TIMEOUT = 30
MAX_WORKERS = 8


class _StaticTokenCredential:
    """Implements Azure TokenCredential protocol with a pre-fetched token."""

    def __init__(self, token: str):
        self._token = AccessToken(token, int(time.time()) + 3600)

    def get_token(self, *scopes, **kwargs):
        return self._token


class AzureOAuthProvider(CloudProvider):
    """Azure provider using Konforme's own app credentials + customer's tenant ID."""

    def __init__(self, tenant_id: str, subscription_id: str):
        self._tenant_id = tenant_id
        self._subscription_id = subscription_id

    def _get_access_token(self) -> str:
        client_id = os.environ.get("AZURE_APP_CLIENT_ID", "")
        client_secret = os.environ.get("AZURE_APP_CLIENT_SECRET", "")

        resp = httpx.post(
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://management.azure.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Azure token request failed: {resp.text}")
        return resp.json()["access_token"]

    def _make_credential(self) -> dict:
        access_token = self._get_access_token()
        return {
            "credential": _StaticTokenCredential(access_token),
            "subscription_id": self._subscription_id,
            "tenant_id": self._tenant_id,
        }

    @property
    def provider_type(self) -> CloudProviderType:
        return CloudProviderType.AZURE

    @property
    def display_name(self) -> str:
        return "Microsoft Azure (OAuth)"

    def run_all_checks(self) -> list[CheckResult]:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        credential = self._make_credential()
        checks = discover_azure_checks()
        all_results: list[CheckResult] = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(check.safe_run, credential): check
                for check in checks
            }
            for future in as_completed(futures, timeout=CHECK_TIMEOUT * len(checks)):
                check = futures[future]
                try:
                    results = future.result(timeout=CHECK_TIMEOUT)
                    all_results.extend(results)
                except Exception as e:
                    logger.error("Azure OAuth check %s failed: %s", check.check_id, e)
                    all_results.append(
                        CheckResult(
                            check_id=check.check_id,
                            title=f"{check.check_id} (timeout)",
                            status="warn",
                            severity=check.severity,
                            message=f"Check timed out after {CHECK_TIMEOUT}s: {e}",
                            provider="azure",
                            nis2_article=check.nis2_article,
                            nis2_requirement=check.nis2_requirement,
                            resource="N/A",
                            domain=check.domain,
                            resource_type="Azure",
                        )
                    )

        return all_results

    def validate_credentials(self) -> bool:
        try:
            self._get_access_token()
            return True
        except Exception as e:
            logger.warning("Azure OAuth validation failed: %s", e)
            return False
