from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from botocore.exceptions import ClientError

from scanner.nis2_mapping import NIS2_MAPPING


class CloudProviderType(str, Enum):
    AWS = "aws"
    AZURE = "azure"


@dataclass
class CheckResult:
    check_id: str
    title: str
    status: str  # pass | fail | warn
    severity: str  # critical | high | medium | low
    message: str
    provider: str = "aws"  # "aws" | "azure"
    nis2_article: str = ""
    nis2_requirement: str = ""
    remediation: str = ""
    resource: str = ""
    remediation_steps: list[str] = field(default_factory=list)
    domain: str = ""
    resource_type: str = ""


class BaseCheck(ABC):
    provider: str = "aws"

    @property
    @abstractmethod
    def check_id(self) -> str: ...

    @property
    @abstractmethod
    def severity(self) -> str: ...

    @property
    def nis2_article(self) -> str:
        mapping = NIS2_MAPPING.get(self.check_id, {})
        return mapping.get("article", "")

    @property
    def nis2_requirement(self) -> str:
        mapping = NIS2_MAPPING.get(self.check_id, {})
        return mapping.get("requirement", "")

    @property
    def domain(self) -> str:
        mapping = NIS2_MAPPING.get(self.check_id, {})
        return mapping.get("domain", "")

    @property
    def article_title(self) -> str:
        mapping = NIS2_MAPPING.get(self.check_id, {})
        return mapping.get("article_title", "")

    @abstractmethod
    def run(self, session: object) -> list[CheckResult]: ...

    def safe_run(self, session: object) -> list[CheckResult]:
        try:
            return self.run(session)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{self.check_id} (access error)",
                    status="warn",
                    severity=self.severity,
                    message=f"AWS API error ({code}): {msg}",
                    provider=self.provider,
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="N/A",
                    domain=self.domain,
                    resource_type="AWS",
                )
            ]
        except Exception as e:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{self.check_id} (error)",
                    status="warn",
                    severity=self.severity,
                    message=f"Unexpected error: {e}",
                    provider=self.provider,
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="N/A",
                    domain=self.domain,
                    resource_type="AWS",
                )
            ]
