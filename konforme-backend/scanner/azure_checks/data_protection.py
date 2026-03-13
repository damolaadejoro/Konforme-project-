"""Azure Data Protection checks — Art 21(2)(d) / Art 21(2)(f) / Art 21(2)(c)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class StorageSecureTransferCheck(AzureCheck):
    check_id = "azure_storage_secure_transfer"
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
            if acct.enable_https_traffic_only:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' requires secure transfer",
                        status="pass",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' requires HTTPS for all traffic.",
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
                        title=f"Storage '{acct.name}' allows insecure transfer",
                        status="fail",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' does not require HTTPS.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable 'Secure transfer required' on storage account '{acct.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Storage Accounts > '{acct.name}' > Configuration",
                            "Set 'Secure transfer required' to Enabled",
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


class SQLAuditingCheck(AzureCheck):
    check_id = "azure_sql_auditing"
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
            try:
                audit_policy = sql_client.server_blob_auditing_policies.get(rg, server.name)
                auditing_enabled = audit_policy.state and str(audit_policy.state).lower() == "enabled"
            except Exception:
                auditing_enabled = False

            if auditing_enabled:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' auditing enabled",
                        status="pass",
                        severity=self.severity,
                        message=f"Auditing is enabled on SQL server '{server.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=server.id or server.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' auditing NOT enabled",
                        status="fail",
                        severity=self.severity,
                        message=f"Auditing is not enabled on SQL server '{server.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable auditing on SQL server '{server.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > SQL servers > '{server.name}' > Auditing",
                            "Enable auditing",
                            "Configure a storage account or Log Analytics workspace",
                            "Save changes",
                        ],
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


class SQLThreatDetectionCheck(AzureCheck):
    check_id = "azure_sql_threat_detection"
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
            try:
                atp = sql_client.server_advanced_threat_protection_settings.get(rg, server.name)
                atp_enabled = atp.state and str(atp.state).lower() == "enabled"
            except Exception:
                atp_enabled = False

            if atp_enabled:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' ATP enabled",
                        status="pass",
                        severity=self.severity,
                        message=f"Advanced Threat Protection is enabled on SQL server '{server.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=server.id or server.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"SQL server '{server.name}' ATP NOT enabled",
                        status="fail",
                        severity=self.severity,
                        message=f"Advanced Threat Protection is not enabled on SQL server '{server.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable ATP on SQL server '{server.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > SQL servers > '{server.name}'",
                            "Navigate to Microsoft Defender for SQL",
                            "Enable Microsoft Defender for SQL",
                            "Configure email recipients for alerts",
                        ],
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


class StorageSoftDeleteCheck(AzureCheck):
    check_id = "azure_storage_soft_delete"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.storage import StorageManagementClient

        storage_client = StorageManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        accounts = list(storage_client.storage_accounts.list())
        results = []

        for acct in accounts:
            rg = acct.id.split("/")[4] if acct.id else ""
            try:
                blob_props = storage_client.blob_services.get_service_properties(rg, acct.name)
                soft_delete = (
                    blob_props.delete_retention_policy
                    and blob_props.delete_retention_policy.enabled
                )
            except Exception:
                soft_delete = None

            if soft_delete:
                days = blob_props.delete_retention_policy.days or 7
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' has soft delete enabled ({days}d)",
                        status="pass",
                        severity=self.severity,
                        message=f"Blob soft delete is enabled on '{acct.name}' with {days}-day retention.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=acct.id or acct.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            elif soft_delete is False:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' does NOT have soft delete",
                        status="fail",
                        severity=self.severity,
                        message=f"Blob soft delete is not enabled on storage account '{acct.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable blob soft delete on storage account '{acct.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Storage Accounts > '{acct.name}' > Data protection",
                            "Enable 'Enable soft delete for blobs'",
                            "Set retention period (e.g., 14 days)",
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
