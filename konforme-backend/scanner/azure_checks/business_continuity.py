"""Azure Incident Response & Business Continuity checks — Art 21(2)(b) / Art 21(2)(c)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class BackupEnabledCheck(AzureCheck):
    check_id = "azure_backup_enabled"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.compute import ComputeManagementClient
        from azure.mgmt.recoveryservices import RecoveryServicesClient

        compute_client = ComputeManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        vms = list(compute_client.virtual_machines.list_all())

        if not vms:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No virtual machines found",
                    status="info",
                    severity=self.severity,
                    message="No virtual machines found in the subscription.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Subscription",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]

        # Check if Recovery Services vaults exist
        try:
            rs_client = RecoveryServicesClient(
                credential=credential["credential"],
                subscription_id=credential["subscription_id"],
            )
            vaults = list(rs_client.vaults.list_by_subscription_id())
            has_vaults = len(vaults) > 0
        except Exception:
            has_vaults = False

        results = []
        if has_vaults:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title=f"Recovery Services vault(s) found ({len(vaults)})",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(vaults)} Recovery Services vault(s) for {len(vms)} VM(s). Verify all VMs are backed up.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title=f"No backup for {len(vms)} VM(s)",
                    status="fail",
                    severity=self.severity,
                    message=f"Found {len(vms)} virtual machine(s) but no Recovery Services vaults for backup.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Create a Recovery Services vault and configure VM backup.",
                    remediation_steps=[
                        "Go to Azure Portal > Recovery Services vaults > Create",
                        "Configure the vault in the same region as your VMs",
                        "Go to Backup > select Azure Virtual Machine",
                        "Add VMs to the backup policy",
                    ],
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            )
        return results


class SQLGeoReplicationCheck(AzureCheck):
    check_id = "azure_sql_geo_replication"
    severity = "medium"

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
                    links = list(sql_client.replication_links.list_by_database(rg, server.name, db.name))
                    has_geo = len(links) > 0
                except Exception:
                    has_geo = False

                # Also check failover groups
                if not has_geo:
                    try:
                        fg = list(sql_client.failover_groups.list_by_server(rg, server.name))
                        has_geo = len(fg) > 0
                    except Exception:
                        pass

                if has_geo:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"SQL '{server.name}/{db.name}' has geo-replication",
                            status="pass",
                            severity=self.severity,
                            message=f"Database '{db.name}' on '{server.name}' has geo-replication or failover group configured.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource=db.id or f"{server.name}/{db.name}",
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            check_id=self.check_id,
                            title=f"SQL '{server.name}/{db.name}' lacks geo-replication",
                            status="fail",
                            severity=self.severity,
                            message=f"Database '{db.name}' on '{server.name}' has no geo-replication or failover group.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            remediation=f"Configure geo-replication for database '{db.name}'.",
                            remediation_steps=[
                                f"Go to Azure Portal > SQL databases > '{db.name}'",
                                "Navigate to Geo-replication",
                                "Select a target region and create a secondary replica",
                                "Or configure a failover group for automatic failover",
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


class AlertRulesCheck(AzureCheck):
    check_id = "azure_alert_rules"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.monitor import MonitorManagementClient

        monitor_client = MonitorManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )

        try:
            metric_alerts = list(monitor_client.metric_alerts.list_by_subscription())
            enabled_alerts = [a for a in metric_alerts if a.enabled]
        except Exception:
            enabled_alerts = []

        if enabled_alerts:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{len(enabled_alerts)} active alert rule(s) found",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(enabled_alerts)} enabled metric alert rule(s).",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="No active alert rules found",
                status="fail",
                severity=self.severity,
                message="No enabled metric alert rules found in the subscription.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Create alert rules for critical metrics and security events.",
                remediation_steps=[
                    "Go to Azure Portal > Monitor > Alerts",
                    "Click 'Create alert rule'",
                    "Select resources and configure conditions (e.g., CPU, security events)",
                    "Configure action groups for notification",
                ],
                resource=f"/subscriptions/{credential['subscription_id']}",
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class ActionGroupsCheck(AzureCheck):
    check_id = "azure_action_groups"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.monitor import MonitorManagementClient

        monitor_client = MonitorManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )

        try:
            action_groups = list(monitor_client.action_groups.list_by_subscription_id())
            enabled_groups = [ag for ag in action_groups if ag.enabled]
        except Exception:
            enabled_groups = []

        if enabled_groups:
            names = [ag.group_short_name or ag.name for ag in enabled_groups]
            return [
                CheckResult(
                    check_id=self.check_id,
                    title=f"{len(enabled_groups)} action group(s) configured",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(enabled_groups)} enabled action group(s): {', '.join(names[:3])}",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=f"/subscriptions/{credential['subscription_id']}",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="No action groups configured",
                status="fail",
                severity=self.severity,
                message="No action groups found. Incident notifications cannot be sent.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Create action groups for incident notification.",
                remediation_steps=[
                    "Go to Azure Portal > Monitor > Action groups",
                    "Click 'Create action group'",
                    "Configure email, SMS, or webhook notifications",
                    "Associate with alert rules",
                ],
                resource=f"/subscriptions/{credential['subscription_id']}",
                domain=self.domain,
                resource_type="Azure",
            )
        ]
