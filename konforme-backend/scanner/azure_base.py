"""Azure-specific base check class."""

from abc import abstractmethod

from scanner.base import BaseCheck, CheckResult
from scanner.nis2_mapping import NIS2_MAPPING


class AzureCheck(BaseCheck):
    """Base class for Azure compliance checks."""

    provider = "azure"

    @abstractmethod
    def run(self, credential) -> list[CheckResult]: ...

    def safe_run(self, credential) -> list[CheckResult]:
        try:
            return self.run(credential)
        except Exception as e:
            error_type = type(e).__name__
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{self.check_id} (error)",
                    status="warn",
                    severity=self.severity,
                    message=f"Azure API error ({error_type}): {e}",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="N/A",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
