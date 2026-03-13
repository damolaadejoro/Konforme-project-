"""Cloud provider abstraction for multi-provider scanning."""

from abc import ABC, abstractmethod

from scanner.base import CheckResult, CloudProviderType


class CloudProvider(ABC):
    """Abstract base class for cloud provider scanning."""

    @property
    @abstractmethod
    def provider_type(self) -> CloudProviderType: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    @abstractmethod
    def run_all_checks(self) -> list[CheckResult]:
        """Run all checks for this provider and return results."""
        ...

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that credentials are working. Returns True if valid."""
        ...
