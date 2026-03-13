"""Azure cloud provider implementation."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.identity import ClientSecretCredential

from scanner.base import CheckResult, CloudProviderType
from scanner.provider import CloudProvider
from scanner.azure_checks import discover_azure_checks

logger = logging.getLogger("konforme.scanner.azure")

CHECK_TIMEOUT = 30
MAX_WORKERS = 8


class AzureProvider(CloudProvider):
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        subscription_id: str,
    ):
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._subscription_id = subscription_id

    @property
    def provider_type(self) -> CloudProviderType:
        return CloudProviderType.AZURE

    @property
    def display_name(self) -> str:
        return "Microsoft Azure"

    def _make_credential(self) -> dict:
        """Create Azure credential dict passed to each check."""
        cred = ClientSecretCredential(
            tenant_id=self._tenant_id,
            client_id=self._client_id,
            client_secret=self._client_secret,
        )
        return {
            "credential": cred,
            "subscription_id": self._subscription_id,
            "tenant_id": self._tenant_id,
        }

    def run_all_checks(self) -> list[CheckResult]:
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
                    logger.error("Azure check %s timed out or failed: %s", check.check_id, e)
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
            cred = ClientSecretCredential(
                tenant_id=self._tenant_id,
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
            # Verify by getting a token for Azure management API
            token = cred.get_token("https://management.azure.com/.default")
            return token is not None
        except Exception as e:
            logger.warning("Azure credential validation failed: %s", e)
            return False
