from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class NACLRulesCheck(BaseCheck):
    check_id = "nacl_rules"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        ec2 = session.client("ec2")
        nacls = ec2.describe_network_acls().get("NetworkAcls", [])

        if not nacls:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No Network ACLs found",
                    status="info",
                    severity=self.severity,
                    message="No Network ACLs found in this region. Not applicable if no VPCs are configured.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="VPC",
                    domain=self.domain,
                    resource_type="VPC",
                )
            ]

        results = []
        for nacl in nacls:
            nacl_id = nacl["NetworkAclId"]
            vpc_id = nacl.get("VpcId", "unknown")
            risky_rules = []

            for entry in nacl.get("Entries", []):
                # Skip egress rules and deny rules
                if entry.get("Egress", False):
                    continue
                if entry.get("RuleAction") != "allow":
                    continue

                cidr = entry.get("CidrBlock", "")
                ipv6_cidr = entry.get("Ipv6CidrBlock", "")
                protocol = entry.get("Protocol", "-1")

                # Check for 0.0.0.0/0 or ::/0 with allow-all
                if (cidr == "0.0.0.0/0" or ipv6_cidr == "::/0") and protocol == "-1":
                    risky_rules.append(
                        f"Rule {entry.get('RuleNumber')}: allows ALL traffic from {cidr or ipv6_cidr}"
                    )

            if risky_rules:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"NACL '{nacl_id}' has overly permissive rules",
                        status="fail",
                        severity=self.severity,
                        message=f"NACL '{nacl_id}' in VPC '{vpc_id}': {'; '.join(risky_rules)}.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Restrict inbound rules on NACL '{nacl_id}'.",
                        remediation_steps=[
                            f"Open VPC console > Network ACLs > {nacl_id}",
                            "Review inbound rules allowing all traffic from 0.0.0.0/0",
                            "Replace with specific port and CIDR ranges",
                            "Keep deny rules to block known malicious ranges",
                        ],
                        resource=f"NACL: {nacl_id}",
                        domain=self.domain,
                        resource_type="VPC",
                    )
                )

        if not results:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Network ACLs are properly configured",
                    status="pass",
                    severity=self.severity,
                    message=f"All {len(nacls)} Network ACL(s) have appropriately scoped inbound rules.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="VPC NACLs",
                    domain=self.domain,
                    resource_type="VPC",
                )
            ]

        return results


class WAFEnabledCheck(BaseCheck):
    check_id = "waf_enabled"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        try:
            waf = session.client("wafv2")
            regional = waf.list_web_acls(Scope="REGIONAL").get("WebACLs", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDeniedException", "WAFNonexistentItemException"):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access AWS WAF",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check AWS WAF configuration.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="WAF",
                        domain=self.domain,
                        resource_type="WAF",
                    )
                ]
            raise

        if not regional:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No WAF Web ACLs configured",
                    status="fail",
                    severity=self.severity,
                    message="No AWS WAF Web ACLs found. Web applications should be protected by WAF rules.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create AWS WAF Web ACLs to protect your web applications.",
                    remediation_steps=[
                        "Open AWS WAF console",
                        "Create a Web ACL with managed rule groups (e.g., AWSManagedRulesCommonRuleSet)",
                        "Associate the Web ACL with your ALB, API Gateway, or CloudFront distribution",
                        "Enable logging for WAF requests",
                    ],
                    resource="WAF",
                    domain=self.domain,
                    resource_type="WAF",
                )
            ]

        return [
            CheckResult(
                check_id=self.check_id,
                title=f"AWS WAF configured ({len(regional)} Web ACL(s))",
                status="pass",
                severity=self.severity,
                message=f"Found {len(regional)} WAF Web ACL(s) for web application protection.",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                resource="WAF",
                domain=self.domain,
                resource_type="WAF",
            )
        ]
