from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class RDSBackupCheck(BaseCheck):
    check_id = "rds_backup"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        client = session.client("rds")
        instances = client.describe_db_instances().get("DBInstances", [])

        if not instances:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No RDS instances found",
                    status="info",
                    severity=self.severity,
                    message="No RDS database instances found in this region.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="RDS",
                    domain=self.domain,
                    resource_type="RDS",
                )
            ]

        results = []
        for db in instances:
            db_id = db["DBInstanceIdentifier"]
            retention = db.get("BackupRetentionPeriod", 0)
            multi_az = db.get("MultiAZ", False)
            encrypted = db.get("StorageEncrypted", False)

            issues = []
            if retention < 7:
                issues.append(f"backup retention is {retention} days (should be >=7)")
            if not multi_az:
                issues.append("Multi-AZ is disabled")
            if not encrypted:
                issues.append("storage is not encrypted")

            if issues:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"RDS '{db_id}' has continuity issues",
                        status="fail",
                        severity=self.severity,
                        message=f"RDS instance '{db_id}': {'; '.join(issues)}.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Fix continuity settings on RDS instance '{db_id}'.",
                        remediation_steps=[
                            f"Open RDS console > Databases > {db_id} > Modify",
                            "Set backup retention period to at least 7 days",
                            "Enable Multi-AZ deployment",
                            "Enable storage encryption (requires recreation if not set at creation)",
                        ],
                        resource=f"RDS: {db_id}",
                        domain=self.domain,
                        resource_type="RDS",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"RDS '{db_id}' has proper backup and continuity",
                        status="pass",
                        severity=self.severity,
                        message=f"RDS instance '{db_id}' has {retention}-day backup retention, Multi-AZ enabled, and encryption enabled.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"RDS: {db_id}",
                        domain=self.domain,
                        resource_type="RDS",
                    )
                )
        return results


class BackupPlanCheck(BaseCheck):
    check_id = "backup_plan"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        try:
            client = session.client("backup")
            plans = client.list_backup_plans().get("BackupPlansList", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDeniedException",):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access AWS Backup",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check AWS Backup plans.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="AWS Backup",
                        domain=self.domain,
                        resource_type="Backup",
                    )
                ]
            raise

        if not plans:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No AWS Backup plans configured",
                    status="fail",
                    severity=self.severity,
                    message="No AWS Backup plans found. Automated backup strategies are required for business continuity.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create an AWS Backup plan to protect critical resources.",
                    remediation_steps=[
                        "Open AWS Backup console",
                        "Click 'Create Backup plan'",
                        "Use a template or create a custom plan",
                        "Assign resources (RDS, EBS, S3, DynamoDB, etc.)",
                        "Set retention period to at least 30 days",
                    ],
                    resource="AWS Backup",
                    domain=self.domain,
                    resource_type="Backup",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title=f"AWS Backup configured ({len(plans)} plan(s))",
                status="pass",
                severity=self.severity,
                message=f"Found {len(plans)} AWS Backup plan(s) for automated backup management.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                resource="AWS Backup",
                domain=self.domain,
                resource_type="Backup",
            )
        ]
