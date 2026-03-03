from scanner.base import BaseCheck, CheckResult


class SNSAlertCheck(BaseCheck):
    check_id = "sns_alerts"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        sns = session.client("sns")
        cloudwatch = session.client("cloudwatch")

        # Check for SNS topics (incident notification channels)
        topics = sns.list_topics().get("Topics", [])
        if not topics:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No SNS topics configured for alerting",
                    status="fail",
                    severity=self.severity,
                    message="No SNS topics found. NIS2 requires incident notification capabilities.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create SNS topics for security alerts and subscribe your security team.",
                    remediation_steps=[
                        "Open SNS console",
                        "Create a topic for security alerts",
                        "Subscribe your security team's email/Slack/PagerDuty",
                        "Configure CloudWatch Alarms to publish to this topic",
                    ],
                    resource="SNS",
                    domain=self.domain,
                    resource_type="SNS",
                )
            ]

        # Check for CloudWatch Alarms (automated incident detection)
        alarms = cloudwatch.describe_alarms(StateValue="OK").get("MetricAlarms", [])
        alarms += cloudwatch.describe_alarms(StateValue="ALARM").get("MetricAlarms", [])

        if not alarms:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No CloudWatch Alarms configured",
                    status="fail",
                    severity=self.severity,
                    message=f"Found {len(topics)} SNS topic(s) but no CloudWatch Alarms. Automated alerting is not configured.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create CloudWatch Alarms for critical security metrics.",
                    remediation_steps=[
                        "Open CloudWatch console > Alarms",
                        "Create alarms for unauthorized API calls, root usage, console sign-in failures",
                        "Link alarms to your SNS security topic",
                    ],
                    resource="CloudWatch",
                    domain=self.domain,
                    resource_type="CloudWatch",
                )
            ]

        # Check if any alarm has an SNS action
        alarms_with_sns = [a for a in alarms if a.get("AlarmActions")]
        if alarms_with_sns:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Security alerting is configured",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(alarms_with_sns)} CloudWatch Alarm(s) with notification actions configured.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="CloudWatch Alarms",
                    domain=self.domain,
                    resource_type="CloudWatch",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title="CloudWatch Alarms have no notification actions",
                status="fail",
                severity=self.severity,
                message="CloudWatch Alarms exist but none have SNS notification actions configured.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Add SNS actions to your CloudWatch Alarms.",
                remediation_steps=[
                    "Open CloudWatch > Alarms",
                    "Edit each alarm",
                    "Add an SNS topic as the notification action",
                ],
                resource="CloudWatch Alarms",
                domain=self.domain,
                resource_type="CloudWatch",
            )
        ]
