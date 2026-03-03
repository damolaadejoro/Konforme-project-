from scanner.base import BaseCheck, CheckResult


class KMSRotationCheck(BaseCheck):
    check_id = "kms_rotation"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("kms")
        keys = client.list_keys().get("Keys", [])
        results = []
        for key in keys:
            key_id = key["KeyId"]
            try:
                meta = client.describe_key(KeyId=key_id)["KeyMetadata"]
                # Skip AWS-managed keys and keys pending deletion
                if meta.get("KeyManager") == "AWS":
                    continue
                if meta.get("KeyState") != "Enabled":
                    continue
                rotation = client.get_key_rotation_status(KeyId=key_id)
                if rotation.get("KeyRotationEnabled", False):
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Key rotation enabled for {key_id[:8]}...",
                            status="pass",
                            severity=self.severity,
                            message=f"KMS key {key_id} has automatic rotation enabled.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=f"KMS Key: {key_id}",
                            domain=self.domain,
                            resource_type="KMS",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Key rotation disabled for {key_id[:8]}...",
                            status="fail",
                            severity=self.severity,
                            message=f"KMS key {key_id} does not have automatic rotation enabled.",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Enable automatic rotation for KMS key {key_id}.",
                            remediation_steps=[
                                "Open KMS console",
                                f"Select key {key_id}",
                                "Go to Key rotation tab",
                                "Enable automatic key rotation",
                            ],
                            resource=f"KMS Key: {key_id}",
                            domain=self.domain,
                            resource_type="KMS",
                        )
                    )
            except Exception:
                continue  # Skip keys we can't inspect
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No customer-managed KMS keys found",
                    status="info",
                    severity=self.severity,
                    message="No customer-managed KMS keys found in this region. AWS-managed keys are in use by default.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create customer-managed KMS keys with automatic rotation enabled.",
                    remediation_steps=[
                        "Open KMS console",
                        "Click 'Create key'",
                        "Choose 'Symmetric' key type",
                        "Enable automatic key rotation",
                        "Use the key for encrypting sensitive resources (S3, EBS, RDS)",
                    ],
                    resource="KMS",
                    domain=self.domain,
                    resource_type="KMS",
                )
            )
        return results


class EBSEncryptionCheck(BaseCheck):
    check_id = "ebs_encryption"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("ec2")
        response = client.get_ebs_encryption_by_default()
        enabled = response.get("EbsEncryptionByDefault", False)
        if enabled:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="EBS default encryption is enabled",
                    status="pass",
                    severity=self.severity,
                    message="EBS volumes are encrypted by default in this region.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="EBS",
                    domain=self.domain,
                    resource_type="EC2",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="EBS default encryption is NOT enabled",
                status="fail",
                severity=self.severity,
                message="EBS volumes are not encrypted by default. New volumes may be created unencrypted.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Enable EBS encryption by default.",
                remediation_steps=[
                    "Open EC2 console",
                    "Go to Settings (under Account attributes)",
                    "Click 'EBS encryption' > 'Manage'",
                    "Enable 'Always encrypt new EBS volumes'",
                    "Save changes",
                ],
                resource="EBS",
                domain=self.domain,
                resource_type="EC2",
            )
        ]
