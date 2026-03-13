"""Azure Logging & Monitoring checks — Art 21(2)(a)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class ActivityLogCheck(AzureCheck):
    check_id = "azure_activity_log"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.monitor import MonitorManagementClient

        monitor_client = MonitorManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        # Check for log profiles or diagnostic settings on the subscription activity log
        log_profiles = list(monitor_client.log_profiles.list())

        if log_profiles:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Activity log export is configured",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(log_profiles)} log profile(s) exporting activity logs.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="Activity log export is NOT configured",
                status="fail",
                severity=self.severity,
                message="No log profiles found. Activity logs are not being exported to storage or Log Analytics.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Configure activity log export to a Log Analytics workspace or storage account.",
                remediation_steps=[
                    "Go to Azure Portal > Monitor > Activity log",
                    "Click 'Export Activity Logs'",
                    "Add a diagnostic setting",
                    "Select a Log Analytics workspace or storage account as the destination",
                ],
                resource=f"/subscriptions/{credential['subscription_id']}",
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class DiagnosticSettingsCheck(AzureCheck):
    check_id = "azure_diagnostic_settings"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.monitor import MonitorManagementClient

        monitor_client = MonitorManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        scope = f"/subscriptions/{credential['subscription_id']}"

        try:
            diag_settings = list(monitor_client.diagnostic_settings.list(resource_uri=scope))
        except Exception:
            diag_settings = []

        if diag_settings:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Subscription diagnostic settings configured",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(diag_settings)} diagnostic setting(s) on the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=scope,
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="No subscription-level diagnostic settings found",
                status="fail",
                severity=self.severity,
                message="No diagnostic settings configured on the subscription level.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Configure diagnostic settings on the subscription.",
                remediation_steps=[
                    "Go to Azure Portal > Subscriptions > Diagnostic settings",
                    "Add a diagnostic setting",
                    "Enable relevant log categories",
                    "Send to a Log Analytics workspace",
                ],
                resource=scope,
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class SecurityCenterCheck(AzureCheck):
    check_id = "azure_security_center"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.security import SecurityCenter

        sec_client = SecurityCenter(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
            asc_location="centralus",
        )

        try:
            pricings = list(sec_client.pricings.list())
            enabled_plans = [p for p in pricings if p.pricing_tier and p.pricing_tier.lower() == "standard"]

            if enabled_plans:
                plan_names = [p.name for p in enabled_plans]
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Microsoft Defender for Cloud is enabled",
                        status="pass",
                        severity=self.severity,
                        message=f"Defender plans enabled: {', '.join(plan_names[:5])}{'...' if len(plan_names) > 5 else ''}",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"/subscriptions/{credential['subscription_id']}",
                        domain=self.domain,
                        resource_type="Azure",
                    )
                ]
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Microsoft Defender for Cloud is NOT fully enabled",
                    status="fail",
                    severity=self.severity,
                    message="No Defender plans are set to Standard tier. Free tier provides limited protection.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable Microsoft Defender for Cloud Standard tier.",
                    remediation_steps=[
                        "Go to Azure Portal > Microsoft Defender for Cloud > Environment settings",
                        "Select your subscription",
                        "Enable Defender plans for Servers, Storage, SQL, etc.",
                        "Save changes",
                    ],
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        except Exception as e:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Could not check Defender for Cloud status",
                    status="warn",
                    severity=self.severity,
                    message=f"Error checking Defender for Cloud: {e}",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]


class LogAnalyticsCheck(AzureCheck):
    check_id = "azure_log_analytics"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.loganalytics import LogAnalyticsManagementClient

        la_client = LogAnalyticsManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        workspaces = list(la_client.workspaces.list())

        if workspaces:
            names = [w.name for w in workspaces]
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"Log Analytics workspace(s) configured",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(workspaces)} Log Analytics workspace(s): {', '.join(names[:3])}",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="No Log Analytics workspaces found",
                status="fail",
                severity=self.severity,
                message="No Log Analytics workspaces found. Centralized logging is not configured.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Create a Log Analytics workspace for centralized logging.",
                remediation_steps=[
                    "Go to Azure Portal > Log Analytics workspaces",
                    "Click 'Create'",
                    "Configure the workspace with appropriate retention",
                    "Connect resources to send logs to this workspace",
                ],
                resource=f"/subscriptions/{credential['subscription_id']}",
                domain=self.domain,
                resource_type="Azure",
            )
        ]
