from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class InspectorEnabledCheck(BaseCheck):
    check_id = "inspector_enabled"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        try:
            inspector = session.client("inspector2")
            status = inspector.batch_get_account_status(
                accountIds=[session.client("sts").get_caller_identity()["Account"]]
            )
            accounts = status.get("accounts", [])
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("AccessDeniedException", "ValidationException"):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access Amazon Inspector",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check Amazon Inspector status.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="Inspector",
                        domain=self.domain,
                        resource_type="Inspector",
                    )
                ]
            raise

        if not accounts:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Amazon Inspector not enabled",
                    status="fail",
                    severity=self.severity,
                    message="Amazon Inspector is not enabled. Vulnerability scanning is required for security testing.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable Amazon Inspector for automated vulnerability scanning.",
                    remediation_steps=[
                        "Open Amazon Inspector console",
                        "Click 'Enable Inspector'",
                        "Enable scanning for EC2 instances, ECR images, and Lambda functions",
                        "Review findings regularly",
                    ],
                    resource="Inspector",
                    domain=self.domain,
                    resource_type="Inspector",
                )
            ]

        acct = accounts[0]
        state = acct.get("state", {}).get("status", "DISABLED")

        if state == "ENABLED":
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Amazon Inspector is enabled",
                    status="pass",
                    severity=self.severity,
                    message="Amazon Inspector is enabled for automated vulnerability scanning.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Inspector",
                    domain=self.domain,
                    resource_type="Inspector",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title=f"Amazon Inspector status: {state}",
                status="fail",
                severity=self.severity,
                message=f"Amazon Inspector is in '{state}' state. It should be fully enabled.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Enable Amazon Inspector for vulnerability scanning.",
                remediation_steps=[
                    "Open Amazon Inspector console",
                    "Click 'Enable Inspector'",
                    "Ensure all resource types are enabled for scanning",
                ],
                resource="Inspector",
                domain=self.domain,
                resource_type="Inspector",
            )
        ]


class ConfigEnabledCheck(BaseCheck):
    check_id = "config_enabled"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        try:
            config = session.client("config")
            recorders = config.describe_configuration_recorders().get("ConfigurationRecorders", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDeniedException",):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access AWS Config",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check AWS Config status.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="Config",
                        domain=self.domain,
                        resource_type="Config",
                    )
                ]
            raise

        if not recorders:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="AWS Config is not enabled",
                    status="fail",
                    severity=self.severity,
                    message="No AWS Config recorders found. Configuration change tracking is required.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable AWS Config to track resource configuration changes.",
                    remediation_steps=[
                        "Open AWS Config console",
                        "Click 'Set up AWS Config'",
                        "Select 'Record all resources'",
                        "Configure an S3 bucket for delivery",
                        "Add conformance packs for NIS2 compliance rules",
                    ],
                    resource="Config",
                    domain=self.domain,
                    resource_type="Config",
                )
            ]

        # Check if recorder is actually recording
        statuses = config.describe_configuration_recorder_status().get(
            "ConfigurationRecordersStatus", []
        )
        recording = any(s.get("recording", False) for s in statuses)

        if not recording:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="AWS Config recorder is not recording",
                    status="fail",
                    severity=self.severity,
                    message="AWS Config recorder exists but is not actively recording configuration changes.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Start the AWS Config recorder.",
                    remediation_steps=[
                        "Open AWS Config console",
                        "Go to Settings",
                        "Ensure the recorder is turned on",
                    ],
                    resource="Config",
                    domain=self.domain,
                    resource_type="Config",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title="AWS Config is enabled and recording",
                status="pass",
                severity=self.severity,
                message="AWS Config is actively recording resource configuration changes.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                resource="Config",
                domain=self.domain,
                resource_type="Config",
            )
        ]
