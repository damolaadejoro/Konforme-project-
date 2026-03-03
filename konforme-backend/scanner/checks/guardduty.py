from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class GuardDutyCheck(BaseCheck):
    check_id = "guardduty_enabled"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        client = session.client("guardduty")
        detectors = client.list_detectors().get("DetectorIds", [])
        if not detectors:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="GuardDuty is not enabled",
                    status="fail",
                    severity=self.severity,
                    message="No GuardDuty detectors found. Threat detection is not active.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable Amazon GuardDuty for threat detection.",
                    remediation_steps=[
                        "Open the GuardDuty console",
                        "Click 'Get Started' or 'Enable GuardDuty'",
                        "Review and confirm settings",
                        "Consider enabling S3 protection and EKS protection",
                    ],
                    resource="AWS Account",
                    domain=self.domain,
                    resource_type="GuardDuty",
                )
            ]
        # Check first detector status
        detector_id = detectors[0]
        detector = client.get_detector(DetectorId=detector_id)
        if detector.get("Status") == "ENABLED":
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="GuardDuty is enabled and active",
                    status="pass",
                    severity=self.severity,
                    message=f"GuardDuty detector {detector_id} is active.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"GuardDuty Detector: {detector_id}",
                    domain=self.domain,
                    resource_type="GuardDuty",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="GuardDuty detector is disabled",
                status="fail",
                severity=self.severity,
                message=f"GuardDuty detector {detector_id} exists but is not enabled.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Re-enable the GuardDuty detector.",
                remediation_steps=[
                    "Open GuardDuty console",
                    f"Select detector {detector_id}",
                    "Enable the detector",
                ],
                resource=f"GuardDuty Detector: {detector_id}",
                domain=self.domain,
                resource_type="GuardDuty",
            )
        ]


class SecurityHubCheck(BaseCheck):
    check_id = "security_hub_enabled"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("securityhub")
        try:
            hub = client.describe_hub()
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Security Hub is enabled",
                    status="pass",
                    severity=self.severity,
                    message=f"Security Hub is active (ARN: {hub.get('HubArn', 'N/A')}).",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=hub.get("HubArn", "Security Hub"),
                    domain=self.domain,
                    resource_type="SecurityHub",
                )
            ]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("InvalidAccessException", "AccessDeniedException"):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Security Hub is not enabled",
                        status="fail",
                        severity=self.severity,
                        message="AWS Security Hub is not enabled in this region.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation="Enable AWS Security Hub for centralized security findings.",
                        remediation_steps=[
                            "Open Security Hub console",
                            "Click 'Go to Security Hub'",
                            "Enable Security Hub",
                            "Enable AWS Foundational Security Best Practices standard",
                        ],
                        resource="AWS Account",
                        domain=self.domain,
                        resource_type="SecurityHub",
                    )
                ]
            raise
