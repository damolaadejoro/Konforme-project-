from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class S3PublicAccessCheck(BaseCheck):
    check_id = "s3_public_access"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        client = session.client("s3")
        buckets = client.list_buckets().get("Buckets", [])
        results = []
        for bucket in buckets:
            name = bucket["Name"]
            try:
                pab = client.get_public_access_block(Bucket=name)
                config = pab["PublicAccessBlockConfiguration"]
                all_blocked = all([
                    config.get("BlockPublicAcls", False),
                    config.get("IgnorePublicAcls", False),
                    config.get("BlockPublicPolicy", False),
                    config.get("RestrictPublicBuckets", False),
                ])
                if all_blocked:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Public access blocked on '{name}'",
                            status="pass",
                            severity=self.severity,
                            message=f"Bucket '{name}' has all public access blocked.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=f"S3 Bucket: {name}",
                            domain=self.domain,
                            resource_type="S3",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Public access NOT fully blocked on '{name}'",
                            status="fail",
                            severity=self.severity,
                            message=f"Bucket '{name}' does not block all public access.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Enable all public access block settings on bucket '{name}'.",
                            remediation_steps=[
                                f"Open S3 console > bucket '{name}' > Permissions",
                                "Click 'Block public access'",
                                "Enable all four block settings",
                                "Save changes",
                            ],
                            resource=f"S3 Bucket: {name}",
                            domain=self.domain,
                            resource_type="S3",
                        )
                    )
            except ClientError:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Public access block not configured on '{name}'",
                        status="fail",
                        severity=self.severity,
                        message=f"Bucket '{name}' has no public access block configuration.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Configure public access block on bucket '{name}'.",
                        remediation_steps=[
                            f"Open S3 console > bucket '{name}' > Permissions",
                            "Configure Block public access settings",
                            "Enable all four block settings",
                        ],
                        resource=f"S3 Bucket: {name}",
                        domain=self.domain,
                        resource_type="S3",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No S3 buckets found",
                    status="pass",
                    severity=self.severity,
                    message="No S3 buckets exist in this account.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="S3",
                    domain=self.domain,
                    resource_type="S3",
                )
            )
        return results


class S3EncryptionCheck(BaseCheck):
    check_id = "s3_encryption"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("s3")
        buckets = client.list_buckets().get("Buckets", [])
        results = []
        for bucket in buckets:
            name = bucket["Name"]
            try:
                enc = client.get_bucket_encryption(Bucket=name)
                rules = enc.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
                if rules:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Encryption enabled on '{name}'",
                            status="pass",
                            severity=self.severity,
                            message=f"Bucket '{name}' has server-side encryption enabled.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=f"S3 Bucket: {name}",
                            domain=self.domain,
                            resource_type="S3",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Encryption not configured on '{name}'",
                            status="fail",
                            severity=self.severity,
                            message=f"Bucket '{name}' does not have server-side encryption.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Enable default encryption on bucket '{name}'.",
                            remediation_steps=[
                                f"Open S3 console > bucket '{name}' > Properties",
                                "Click 'Default encryption'",
                                "Enable SSE-S3 or SSE-KMS",
                                "Save changes",
                            ],
                            resource=f"S3 Bucket: {name}",
                            domain=self.domain,
                            resource_type="S3",
                        )
                    )
            except ClientError:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Encryption not enabled on '{name}'",
                        status="fail",
                        severity=self.severity,
                        message=f"Bucket '{name}' does not have default encryption configured.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable default encryption on bucket '{name}'.",
                        remediation_steps=[
                            f"Open S3 > '{name}' > Properties > Default encryption",
                            "Enable SSE-S3 or SSE-KMS encryption",
                        ],
                        resource=f"S3 Bucket: {name}",
                        domain=self.domain,
                        resource_type="S3",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No S3 buckets found",
                    status="pass",
                    severity=self.severity,
                    message="No S3 buckets exist in this account.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="S3",
                    domain=self.domain,
                    resource_type="S3",
                )
            )
        return results


class S3VersioningCheck(BaseCheck):
    check_id = "s3_versioning"
    severity = "low"

    def run(self, session) -> list[CheckResult]:
        client = session.client("s3")
        buckets = client.list_buckets().get("Buckets", [])
        results = []
        for bucket in buckets:
            name = bucket["Name"]
            versioning = client.get_bucket_versioning(Bucket=name)
            status = versioning.get("Status", "Disabled")
            if status == "Enabled":
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Versioning enabled on '{name}'",
                        status="pass",
                        severity=self.severity,
                        message=f"Bucket '{name}' has versioning enabled for backup/recovery.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"S3 Bucket: {name}",
                        domain=self.domain,
                        resource_type="S3",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Versioning not enabled on '{name}'",
                        status="fail",
                        severity=self.severity,
                        message=f"Bucket '{name}' does not have versioning enabled.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable versioning on bucket '{name}'.",
                        remediation_steps=[
                            f"Open S3 console > bucket '{name}' > Properties",
                            "Click 'Bucket Versioning'",
                            "Enable versioning",
                            "Save changes",
                        ],
                        resource=f"S3 Bucket: {name}",
                        domain=self.domain,
                        resource_type="S3",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No S3 buckets found",
                    status="pass",
                    severity=self.severity,
                    message="No S3 buckets exist in this account.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="S3",
                    domain=self.domain,
                    resource_type="S3",
                )
            )
        return results
