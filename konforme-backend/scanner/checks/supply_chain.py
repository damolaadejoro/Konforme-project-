from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class ECRScanningCheck(BaseCheck):
    check_id = "ecr_scanning"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        try:
            ecr = session.client("ecr")
            repos = ecr.describe_repositories().get("repositories", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDeniedException",):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access ECR",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check ECR scanning configuration.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="ECR",
                        domain=self.domain,
                        resource_type="ECR",
                    )
                ]
            raise

        if not repos:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No ECR repositories found",
                    status="info",
                    severity=self.severity,
                    message="No ECR repositories found in this region. Not applicable if you don't use container images.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="ECR",
                    domain=self.domain,
                    resource_type="ECR",
                )
            ]

        unscanned = []
        for repo in repos:
            repo_name = repo["repositoryName"]
            scan_config = repo.get("imageScanningConfiguration", {})
            if not scan_config.get("scanOnPush", False):
                unscanned.append(repo_name)

        if unscanned:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{len(unscanned)} ECR repo(s) without scan-on-push",
                    status="fail",
                    severity=self.severity,
                    message=f"Repositories without scan-on-push: {', '.join(unscanned[:5])}{'...' if len(unscanned) > 5 else ''}.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable scan-on-push for all ECR repositories.",
                    remediation_steps=[
                        "Open ECR console > Repositories",
                        "Select each repository > Edit",
                        "Enable 'Scan on push'",
                        "Or enable enhanced scanning via Amazon Inspector for continuous monitoring",
                    ],
                    resource="ECR",
                    domain=self.domain,
                    resource_type="ECR",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title=f"All {len(repos)} ECR repo(s) have scan-on-push enabled",
                status="pass",
                severity=self.severity,
                message=f"All {len(repos)} ECR repositories have image scanning enabled on push.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                resource="ECR",
                domain=self.domain,
                resource_type="ECR",
            )
        ]
