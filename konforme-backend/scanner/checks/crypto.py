from botocore.exceptions import ClientError

from scanner.base import BaseCheck, CheckResult


class ACMCertificatesCheck(BaseCheck):
    check_id = "acm_certificates"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        acm = session.client("acm")
        certs = acm.list_certificates().get("CertificateSummaryList", [])

        if not certs:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No ACM certificates found",
                    status="info",
                    severity=self.severity,
                    message="No ACM certificates found in this region. Not applicable if you don't use HTTPS services here.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="ACM",
                    domain=self.domain,
                    resource_type="ACM",
                )
            ]

        results = []
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        expiring_soon = []
        expired = []

        for cert in certs:
            domain = cert.get("DomainName", "unknown")
            status = cert.get("Status", "UNKNOWN")
            not_after = cert.get("NotAfter")

            if status == "EXPIRED":
                expired.append(domain)
            elif not_after:
                days_left = (not_after - now).days
                if days_left < 30:
                    expiring_soon.append(f"{domain} ({days_left} days)")

        if expired:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title=f"{len(expired)} expired ACM certificate(s)",
                    status="fail",
                    severity=self.severity,
                    message=f"Expired certificates: {', '.join(expired)}.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Renew or replace expired ACM certificates.",
                    remediation_steps=[
                        "Open ACM console",
                        "Identify expired certificates",
                        "Request new certificates or enable auto-renewal",
                        "Update resources to use the new certificates",
                    ],
                    resource="ACM",
                    domain=self.domain,
                    resource_type="ACM",
                )
            )

        if expiring_soon:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title=f"{len(expiring_soon)} ACM certificate(s) expiring soon",
                    status="fail",
                    severity="medium",
                    message=f"Certificates expiring within 30 days: {', '.join(expiring_soon)}.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Renew ACM certificates before they expire.",
                    remediation_steps=[
                        "Open ACM console",
                        "Check certificates expiring soon",
                        "Enable auto-renewal if using DNS validation",
                        "Manually renew if using email validation",
                    ],
                    resource="ACM",
                    domain=self.domain,
                    resource_type="ACM",
                )
            )

        if not results:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"All {len(certs)} ACM certificate(s) are valid",
                    status="pass",
                    severity=self.severity,
                    message=f"All {len(certs)} ACM certificate(s) are valid and not expiring within 30 days.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="ACM",
                    domain=self.domain,
                    resource_type="ACM",
                )
            ]

        return results


class ELBTLSCheck(BaseCheck):
    check_id = "elb_tls"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        try:
            elbv2 = session.client("elbv2")
            lbs = elbv2.describe_load_balancers().get("LoadBalancers", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ("AccessDeniedException",):
                return [
                    CheckResult(
                        check_id=self.check_id,
                        title="Cannot access ELB",
                        status="warn",
                        severity=self.severity,
                        message="Insufficient permissions to check load balancer TLS configuration.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource="ELB",
                        domain=self.domain,
                        resource_type="ELB",
                    )
                ]
            raise

        if not lbs:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No load balancers found",
                    status="info",
                    severity=self.severity,
                    message="No Application/Network Load Balancers found in this region. Not applicable if you don't use load balancers.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="ELB",
                    domain=self.domain,
                    resource_type="ELB",
                )
            ]

        results = []
        for lb in lbs:
            lb_name = lb["LoadBalancerName"]
            lb_arn = lb["LoadBalancerArn"]

            listeners = elbv2.describe_listeners(LoadBalancerArn=lb_arn).get("Listeners", [])

            has_https = False
            insecure_listeners = []

            for listener in listeners:
                protocol = listener.get("Protocol", "")
                if protocol in ("HTTPS", "TLS"):
                    has_https = True
                    ssl_policy = listener.get("SslPolicy", "")
                    # Flag outdated TLS policies
                    if ssl_policy and ("TLS-1-0" in ssl_policy or "TLS-1-1" in ssl_policy):
                        insecure_listeners.append(
                            f"Port {listener.get('Port')}: uses outdated policy {ssl_policy}"
                        )
                elif protocol in ("HTTP",):
                    # HTTP listener without redirect is a concern
                    actions = listener.get("DefaultActions", [])
                    is_redirect = any(a.get("Type") == "redirect" for a in actions)
                    if not is_redirect:
                        insecure_listeners.append(
                            f"Port {listener.get('Port')}: HTTP without HTTPS redirect"
                        )

            if insecure_listeners:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Load balancer '{lb_name}' has TLS issues",
                        status="fail",
                        severity=self.severity,
                        message=f"LB '{lb_name}': {'; '.join(insecure_listeners)}.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Fix TLS configuration on '{lb_name}'.",
                        remediation_steps=[
                            f"Open EC2 > Load Balancers > {lb_name} > Listeners",
                            "Add HTTPS listener with TLS 1.2+ policy",
                            "Redirect HTTP to HTTPS",
                            "Use security policy ELBSecurityPolicy-TLS13-1-2-2021-06 or newer",
                        ],
                        resource=f"ELB: {lb_name}",
                        domain=self.domain,
                        resource_type="ELB",
                    )
                )
            elif not has_https and listeners:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Load balancer '{lb_name}' has no HTTPS listeners",
                        status="fail",
                        severity=self.severity,
                        message=f"LB '{lb_name}' has no HTTPS/TLS listeners. All traffic should be encrypted in transit.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Add HTTPS listener to '{lb_name}'.",
                        remediation_steps=[
                            f"Open EC2 > Load Balancers > {lb_name} > Listeners",
                            "Add HTTPS listener on port 443",
                            "Attach an ACM certificate",
                            "Redirect HTTP (port 80) to HTTPS",
                        ],
                        resource=f"ELB: {lb_name}",
                        domain=self.domain,
                        resource_type="ELB",
                    )
                )

        if not results:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"All {len(lbs)} load balancer(s) have proper TLS",
                    status="pass",
                    severity=self.severity,
                    message=f"All {len(lbs)} load balancer(s) have HTTPS/TLS listeners with modern security policies.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="ELB",
                    domain=self.domain,
                    resource_type="ELB",
                )
            ]

        return results
