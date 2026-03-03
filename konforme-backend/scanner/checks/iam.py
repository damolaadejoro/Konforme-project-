from datetime import datetime, timezone

from scanner.base import BaseCheck, CheckResult


class RootMFACheck(BaseCheck):
    check_id = "root_mfa"
    severity = "critical"

    def run(self, session) -> list[CheckResult]:
        client = session.client("iam")
        summary = client.get_account_summary()["SummaryMap"]
        mfa_enabled = summary.get("AccountMFAEnabled", 0)
        if mfa_enabled:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Root account MFA is enabled",
                    status="pass",
                    severity=self.severity,
                    message="The root account has MFA enabled.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Root Account",
                    domain=self.domain,
                    resource_type="IAM",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="Root account MFA is NOT enabled",
                status="fail",
                severity=self.severity,
                message="The root account does not have MFA enabled. This is a critical security risk.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Enable MFA on the root account immediately.",
                remediation_steps=[
                    "Sign in as root user",
                    "Go to IAM > Security credentials",
                    "Under MFA, click 'Assign MFA device'",
                    "Use a hardware token or authenticator app",
                ],
                resource="Root Account",
                domain=self.domain,
                resource_type="IAM",
            )
        ]


class NoRootKeysCheck(BaseCheck):
    check_id = "no_root_access_keys"
    severity = "critical"

    def run(self, session) -> list[CheckResult]:
        client = session.client("iam")
        summary = client.get_account_summary()["SummaryMap"]
        root_keys = summary.get("AccountAccessKeysPresent", 0)
        if root_keys == 0:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No root access keys found",
                    status="pass",
                    severity=self.severity,
                    message="The root account has no access keys, which is the recommended configuration.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Root Account",
                    domain=self.domain,
                    resource_type="IAM",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="Root account has active access keys",
                status="fail",
                severity=self.severity,
                message="Root access keys exist. These provide unrestricted access and should be deleted.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Delete root account access keys and use IAM users instead.",
                remediation_steps=[
                    "Sign in as root user",
                    "Go to Security credentials",
                    "Delete all access keys",
                    "Create IAM users with appropriate permissions",
                ],
                resource="Root Account",
                domain=self.domain,
                resource_type="IAM",
            )
        ]


class OldAccessKeysCheck(BaseCheck):
    check_id = "old_access_keys"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("iam")
        users = client.list_users().get("Users", [])
        results = []
        now = datetime.now(timezone.utc)
        for user in users:
            username = user["UserName"]
            keys = client.list_access_keys(UserName=username).get("AccessKeyMetadata", [])
            for key in keys:
                if key["Status"] != "Active":
                    continue
                age_days = (now - key["CreateDate"].replace(tzinfo=timezone.utc)).days
                if age_days > 90:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Access key for '{username}' is {age_days} days old",
                            status="fail",
                            severity=self.severity,
                            message=f"Access key {key['AccessKeyId']} for user '{username}' is {age_days} days old (>90 days).",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Rotate access key for user '{username}'.",
                            remediation_steps=[
                                f"Create a new access key for '{username}'",
                                "Update applications to use the new key",
                                f"Deactivate old key {key['AccessKeyId']}",
                                "Delete the old key after confirming apps work",
                            ],
                            resource=f"IAM User: {username}",
                            domain=self.domain,
                            resource_type="IAM",
                        )
                    )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="All access keys are within rotation policy",
                    status="pass",
                    severity=self.severity,
                    message="No access keys older than 90 days were found.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="IAM Users",
                    domain=self.domain,
                    resource_type="IAM",
                )
            )
        return results


class MFAUsersCheck(BaseCheck):
    check_id = "mfa_users"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("iam")
        users = client.list_users().get("Users", [])
        results = []
        for user in users:
            username = user["UserName"]
            # Check if user has console access (login profile)
            try:
                client.get_login_profile(UserName=username)
            except client.exceptions.NoSuchEntityException:
                continue  # no console access, skip
            mfa_devices = client.list_mfa_devices(UserName=username).get("MFADevices", [])
            if mfa_devices:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"MFA enabled for '{username}'",
                        status="pass",
                        severity=self.severity,
                        message=f"User '{username}' has MFA enabled.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"IAM User: {username}",
                        domain=self.domain,
                        resource_type="IAM",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"MFA NOT enabled for '{username}'",
                        status="fail",
                        severity=self.severity,
                        message=f"User '{username}' has console access but no MFA device.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable MFA for user '{username}'.",
                        remediation_steps=[
                            f"Go to IAM > Users > {username} > Security credentials",
                            "Click 'Assign MFA device'",
                            "Choose virtual or hardware MFA",
                            "Complete the setup process",
                        ],
                        resource=f"IAM User: {username}",
                        domain=self.domain,
                        resource_type="IAM",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No IAM users with console access found",
                    status="info",
                    severity=self.severity,
                    message="No IAM users with console access were found. Consider creating dedicated IAM users with MFA instead of using root.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="IAM Users",
                    domain=self.domain,
                    resource_type="IAM",
                )
            )
        return results
