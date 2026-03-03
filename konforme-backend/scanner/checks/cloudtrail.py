from scanner.base import BaseCheck, CheckResult


class CloudTrailEnabledCheck(BaseCheck):
    check_id = "cloudtrail_enabled"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        client = session.client("cloudtrail")
        trails = client.describe_trails().get("trailList", [])
        if not trails:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="CloudTrail is not enabled",
                    status="fail",
                    severity=self.severity,
                    message="No CloudTrail trails found. Audit logging is required for NIS2 compliance.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable CloudTrail in all regions with management events logging.",
                    remediation_steps=[
                        "Open the CloudTrail console",
                        "Create a new trail with multi-region enabled",
                        "Configure an S3 bucket for log storage",
                        "Enable management events logging",
                    ],
                    resource="AWS Account",
                    domain=self.domain,
                    resource_type="CloudTrail",
                )
            ]
        # Check if any trail is multi-region and logging
        results = []
        for trail in trails:
            name = trail.get("Name", "unknown")
            status = client.get_trail_status(Name=trail["TrailARN"])
            is_logging = status.get("IsLogging", False)
            is_multi = trail.get("IsMultiRegionTrail", False)
            if is_logging and is_multi:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"CloudTrail '{name}' is active and multi-region",
                        status="pass",
                        severity=self.severity,
                        message=f"Trail '{name}' is logging and covers all regions.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=trail["TrailARN"],
                        domain=self.domain,
                        resource_type="CloudTrail",
                    )
                )
            else:
                issues = []
                if not is_logging:
                    issues.append("not logging")
                if not is_multi:
                    issues.append("not multi-region")
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"CloudTrail '{name}' has issues: {', '.join(issues)}",
                        status="fail",
                        severity=self.severity,
                        message=f"Trail '{name}' is {', '.join(issues)}.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation="Ensure the trail is logging and multi-region is enabled.",
                        remediation_steps=[
                            "Open CloudTrail console",
                            f"Select trail '{name}'",
                            "Enable logging if stopped",
                            "Enable multi-region trail option",
                        ],
                        resource=trail["TrailARN"],
                        domain=self.domain,
                        resource_type="CloudTrail",
                    )
                )
        return results


class CloudTrailValidationCheck(BaseCheck):
    check_id = "cloudtrail_log_validation"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("cloudtrail")
        trails = client.describe_trails().get("trailList", [])
        if not trails:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No CloudTrail trails for log validation check",
                    status="fail",
                    severity=self.severity,
                    message="No trails exist to validate log file integrity.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create a CloudTrail trail with log file validation enabled.",
                    remediation_steps=["Create a CloudTrail trail", "Enable log file validation"],
                    resource="AWS Account",
                    domain=self.domain,
                    resource_type="CloudTrail",
                )
            ]
        results = []
        for trail in trails:
            name = trail.get("Name", "unknown")
            if trail.get("LogFileValidationEnabled", False):
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Log validation enabled on '{name}'",
                        status="pass",
                        severity=self.severity,
                        message=f"Trail '{name}' has log file integrity validation enabled.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=trail["TrailARN"],
                        domain=self.domain,
                        resource_type="CloudTrail",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Log validation disabled on '{name}'",
                        status="fail",
                        severity=self.severity,
                        message=f"Trail '{name}' does not have log file validation. Logs could be tampered with.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation="Enable log file validation on this CloudTrail trail.",
                        remediation_steps=[
                            "Open CloudTrail console",
                            f"Edit trail '{name}'",
                            "Enable 'Log file validation'",
                            "Save changes",
                        ],
                        resource=trail["TrailARN"],
                        domain=self.domain,
                        resource_type="CloudTrail",
                    )
                )
        return results
