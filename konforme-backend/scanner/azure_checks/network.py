"""Azure Network Security checks — Art 21(2)(e)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class NSGUnrestrictedCheck(AzureCheck):
    check_id = "azure_nsg_unrestricted"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.network import NetworkManagementClient

        net_client = NetworkManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        nsgs = list(net_client.network_security_groups.list_all())
        results = []
        dangerous_ports = {"22", "3389", "445", "1433", "3306", "5432"}

        for nsg in nsgs:
            issues = []
            for rule in (nsg.security_rules or []):
                if rule.direction != "Inbound" or rule.access != "Allow":
                    continue
                src = rule.source_address_prefix or ""
                if src in ("*", "0.0.0.0/0", "Internet"):
                    port_range = rule.destination_port_range or ""
                    if port_range == "*" or port_range in dangerous_ports:
                        issues.append(f"Rule '{rule.name}' allows {src} to port {port_range}")

            if issues:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"NSG '{nsg.name}' allows unrestricted inbound",
                        status="fail",
                        severity=self.severity,
                        message=f"NSG '{nsg.name}' has {len(issues)} rule(s) allowing unrestricted inbound: {'; '.join(issues[:3])}",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Restrict inbound rules on NSG '{nsg.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Network Security Groups > '{nsg.name}'",
                            "Review inbound security rules",
                            "Replace '0.0.0.0/0' or '*' with specific IP ranges",
                            "Restrict access to management ports (22, 3389)",
                        ],
                        resource=nsg.id or nsg.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"NSG '{nsg.name}' has no unrestricted inbound rules",
                        status="pass",
                        severity=self.severity,
                        message=f"NSG '{nsg.name}' does not allow unrestricted inbound access on sensitive ports.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=nsg.id or nsg.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No Network Security Groups found",
                    status="info",
                    severity=self.severity,
                    message="No NSGs found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class SQLFirewallCheck(AzureCheck):
    check_id = "azure_sql_firewall"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.sql import SqlManagementClient

        sql_client = SqlManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        servers = list(sql_client.servers.list())
        results = []

        for server in servers:
            rg = server.id.split("/")[4] if server.id else ""
            fw_rules = list(sql_client.firewall_rules.list_by_server(rg, server.name))
            open_rules = [
                r for r in fw_rules
                if r.start_ip_address == "0.0.0.0" and r.end_ip_address == "255.255.255.255"
            ]

            if open_rules:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' allows all IPs",
                        status="fail",
                        severity=self.severity,
                        message=f"SQL server '{server.name}' has firewall rule(s) allowing 0.0.0.0 — 255.255.255.255.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Restrict firewall rules on SQL server '{server.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > SQL servers > '{server.name}' > Networking",
                            "Remove or restrict rules allowing 0.0.0.0/0",
                            "Add specific IP ranges for trusted clients",
                            "Consider using Private Endpoints",
                        ],
                        resource=server.id or server.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' has restricted firewall",
                        status="pass",
                        severity=self.severity,
                        message=f"SQL server '{server.name}' does not allow unrestricted network access.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=server.id or server.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No SQL servers found",
                    status="info",
                    severity=self.severity,
                    message="No SQL servers found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class StoragePublicAccessCheck(AzureCheck):
    check_id = "azure_storage_public_access"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.storage import StorageManagementClient

        storage_client = StorageManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        accounts = list(storage_client.storage_accounts.list())
        results = []

        for acct in accounts:
            public_access = acct.allow_blob_public_access
            if public_access is False:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' blocks public access",
                        status="pass",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' has public blob access disabled.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=acct.id or acct.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' allows public access",
                        status="fail",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' allows public blob access.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Disable public access on storage account '{acct.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Storage Accounts > '{acct.name}' > Configuration",
                            "Set 'Allow Blob public access' to Disabled",
                            "Save changes",
                        ],
                        resource=acct.id or acct.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No storage accounts found",
                    status="info",
                    severity=self.severity,
                    message="No storage accounts found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class AppServiceHTTPSCheck(AzureCheck):
    check_id = "azure_app_service_https"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.web import WebSiteManagementClient

        web_client = WebSiteManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        apps = list(web_client.web_apps.list())
        results = []

        for app in apps:
            https_only = app.https_only
            if https_only:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"App Service '{app.name}' enforces HTTPS",
                        status="pass",
                        severity=self.severity,
                        message=f"App Service '{app.name}' has HTTPS Only enabled.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=app.id or app.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"App Service '{app.name}' does NOT enforce HTTPS",
                        status="fail",
                        severity=self.severity,
                        message=f"App Service '{app.name}' allows HTTP traffic.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable HTTPS Only on App Service '{app.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > App Services > '{app.name}' > TLS/SSL settings",
                            "Set 'HTTPS Only' to On",
                            "Save changes",
                        ],
                        resource=app.id or app.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No App Services found",
                    status="info",
                    severity=self.severity,
                    message="No App Services found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results
