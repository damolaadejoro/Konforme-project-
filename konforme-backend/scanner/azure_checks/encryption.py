"""Azure Encryption checks — Art 21(2)(d) / Art 21(2)(h)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class StorageEncryptionCheck(AzureCheck):
    check_id = "azure_storage_encryption"
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
            enc = acct.encryption
            uses_cmk = (
                enc and enc.key_source and enc.key_source.lower() == "microsoft.keyvault"
            )
            if uses_cmk:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Storage '{acct.name}' uses customer-managed keys",
                        status="pass",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' uses customer-managed encryption keys.",
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
                        title=f"Storage '{acct.name}' uses Microsoft-managed keys",
                        status="warn",
                        severity=self.severity,
                        message=f"Storage account '{acct.name}' uses Microsoft-managed keys. Consider customer-managed keys for compliance.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Configure customer-managed keys for storage account '{acct.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Storage Accounts > '{acct.name}' > Encryption",
                            "Select 'Customer-managed keys'",
                            "Choose or create a Key Vault and key",
                            "Save the configuration",
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


class DiskEncryptionCheck(AzureCheck):
    check_id = "azure_disk_encryption"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.compute import ComputeManagementClient

        compute_client = ComputeManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        disks = list(compute_client.disks.list())
        results = []

        for disk in disks:
            encrypted = disk.encryption and disk.encryption.type and "EncryptionAtRestWithCustomerKey" in str(disk.encryption.type)
            platform_encrypted = disk.encryption and disk.encryption.type and "EncryptionAtRestWithPlatformKey" in str(disk.encryption.type)

            if encrypted:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Disk '{disk.name}' is encrypted with CMK",
                        status="pass",
                        severity=self.severity,
                        message=f"Disk '{disk.name}' uses customer-managed key encryption.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=disk.id or disk.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            elif platform_encrypted:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Disk '{disk.name}' uses platform encryption",
                        status="pass",
                        severity=self.severity,
                        message=f"Disk '{disk.name}' uses platform-managed encryption (default). Consider CMK for higher compliance.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=disk.id or disk.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Disk '{disk.name}' encryption status unknown",
                        status="warn",
                        severity=self.severity,
                        message=f"Could not determine encryption status of disk '{disk.name}'.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Verify encryption on disk '{disk.name}'.",
                        resource=disk.id or disk.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No managed disks found",
                    status="info",
                    severity=self.severity,
                    message="No managed disks found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class SQLTDECheck(AzureCheck):
    check_id = "azure_sql_tde"
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
            dbs = list(sql_client.databases.list_by_server(rg, server.name))
            for db in dbs:
                if db.name == "master":
                    continue
                try:
                    tde = sql_client.transparent_data_encryptions.get(
                        rg, server.name, db.name, "current"
                    )
                    tde_enabled = tde.status and str(tde.status).lower() == "enabled"
                except Exception:
                    tde_enabled = None

                if tde_enabled:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"TDE enabled on '{server.name}/{db.name}'",
                            status="pass",
                            severity=self.severity,
                            message=f"Transparent Data Encryption is enabled on database '{db.name}' on server '{server.name}'.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=db.id or f"{server.name}/{db.name}",
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    )
                elif tde_enabled is False:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"TDE NOT enabled on '{server.name}/{db.name}'",
                            status="fail",
                            severity=self.severity,
                            message=f"Transparent Data Encryption is disabled on database '{db.name}' on server '{server.name}'.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Enable TDE on database '{db.name}'.",
                            remediation_steps=[
                                f"Go to Azure Portal > SQL databases > '{db.name}'",
                                "Navigate to Transparent data encryption",
                                "Enable data encryption",
                            ],
                            resource=db.id or f"{server.name}/{db.name}",
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No SQL databases found",
                    status="info",
                    severity=self.severity,
                    message="No SQL databases found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class KeyVaultExpiryCheck(AzureCheck):
    check_id = "azure_key_vault_expiry"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.keyvault import KeyVaultManagementClient

        kv_client = KeyVaultManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        vaults = list(kv_client.vaults.list())
        results = []

        for vault in vaults:
            rg = vault.id.split("/")[4] if vault.id else ""
            try:
                full_vault = kv_client.vaults.get(rg, vault.name)
                vault_uri = full_vault.properties.vault_uri

                from azure.keyvault.keys import KeyClient
                from azure.keyvault.secrets import SecretClient

                key_client = KeyClient(vault_url=vault_uri, credential=credential["credential"])
                keys_without_expiry = []
                for key_props in key_client.list_properties_of_keys():
                    if key_props.expires_on is None and key_props.enabled:
                        keys_without_expiry.append(key_props.name)

                secret_client = SecretClient(vault_url=vault_uri, credential=credential["credential"])
                secrets_without_expiry = []
                for secret_props in secret_client.list_properties_of_secrets():
                    if secret_props.expires_on is None and secret_props.enabled:
                        secrets_without_expiry.append(secret_props.name)

                issues = keys_without_expiry + secrets_without_expiry
                if not issues:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Key Vault '{vault.name}' — all keys/secrets have expiry",
                            status="pass",
                            severity=self.severity,
                            message=f"All enabled keys and secrets in '{vault.name}' have expiration dates.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=vault.id or vault.name,
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"Key Vault '{vault.name}' has items without expiry",
                            status="fail",
                            severity=self.severity,
                            message=f"'{vault.name}' has {len(keys_without_expiry)} key(s) and {len(secrets_without_expiry)} secret(s) without expiration dates.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Set expiration dates on all keys and secrets in '{vault.name}'.",
                            remediation_steps=[
                                f"Go to Azure Portal > Key Vault '{vault.name}'",
                                "Review each key and secret",
                                "Set appropriate expiration dates",
                                "Implement key rotation procedures",
                            ],
                            resource=vault.id or vault.name,
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    )
            except Exception as e:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Could not check Key Vault '{vault.name}'",
                        status="warn",
                        severity=self.severity,
                        message=f"Error accessing Key Vault '{vault.name}': {e}",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=vault.id or vault.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No Key Vaults found",
                    status="info",
                    severity=self.severity,
                    message="No Key Vaults found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results
