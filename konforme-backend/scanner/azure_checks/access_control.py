"""Azure Access Control checks — Art 21(2)(i)."""

from scanner.azure_base import AzureCheck
from scanner.base import CheckResult


class MFAEnforcedCheck(AzureCheck):
    check_id = "azure_mfa_enforced"
    severity = "critical"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.resource import ResourceManagementClient
        from azure.identity import ClientSecretCredential

        # Check if Conditional Access policies exist requiring MFA
        # We verify by checking if Security Defaults or CA policies are in place
        # via Microsoft Graph (requires Directory.Read.All)
        try:
            from msgraph.core import GraphClient
            graph = GraphClient(credential=credential["credential"])
            # Check conditional access policies
            resp = graph.get("/identity/conditionalAccess/policies")
            policies = resp.json().get("value", [])
            mfa_policies = [
                p for p in policies
                if p.get("state") == "enabled"
                and any(
                    gc.get("builtInControls", [])
                    for gc in p.get("grantControls", {}).get("builtInControls", [])
                    if "mfa" in gc
                )
            ]
        except Exception:
            # If we can't check Graph, fall back to checking Security Center recommendations
            from azure.mgmt.security import SecurityCenter
            try:
                sec_client = SecurityCenter(
                    credential=credential["credential"],
                    subscription_id=credential["subscription_id"],
                    asc_location="centralus",
                )
                assessments = list(sec_client.assessments.list(scope=f"/subscriptions/{credential['subscription_id']}"))
                mfa_assessment = None
                for a in assessments:
                    if a.display_name and "MFA" in a.display_name.upper():
                        mfa_assessment = a
                        break
                if mfa_assessment and mfa_assessment.status and mfa_assessment.status.code == "Healthy":
                    return [
                        CheckResult(
                            check_id=self.check_id,
                            title="MFA is enforced",
                            status="pass",
                            severity=self.severity,
                            message="MFA enforcement is detected via Security Center assessment.",
                            provider="azure",
                            nis2_article=self.nis2_article,
                            nis2_requirement=self.nis2_requirement,
                            resource="Azure AD",
                            domain=self.domain,
                            resource_type="Azure",
                        )
                    ]
            except Exception:
                pass

            return [
                CheckResult(
                    check_id=self.check_id,
                    title="MFA enforcement could not be verified",
                    status="warn",
                    severity=self.severity,
                    message="Unable to verify MFA enforcement. Ensure Conditional Access policies or Security Defaults require MFA.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    remediation="Enable Security Defaults or create a Conditional Access policy requiring MFA for all users.",
                    remediation_steps=[
                        "Go to Azure Portal > Azure Active Directory > Properties",
                        "Click 'Manage Security defaults' and enable, OR",
                        "Create a Conditional Access policy requiring MFA",
                        "Apply to all users and cloud apps",
                    ],
                    resource="Azure AD",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]

        if mfa_policies:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="MFA is enforced via Conditional Access",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(mfa_policies)} active Conditional Access policy/policies requiring MFA.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="Azure AD",
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title="No MFA enforcement detected",
                status="fail",
                severity=self.severity,
                message="No Conditional Access policies requiring MFA were found.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Create a Conditional Access policy requiring MFA for all users.",
                remediation_steps=[
                    "Go to Azure Portal > Azure AD > Security > Conditional Access",
                    "Create a new policy targeting all users",
                    "Under Grant, select 'Require multi-factor authentication'",
                    "Enable the policy",
                ],
                resource="Azure AD",
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class NoClassicAdminsCheck(AzureCheck):
    check_id = "azure_no_classic_admins"
    severity = "high"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.authorization import AuthorizationManagementClient

        auth_client = AuthorizationManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        scope = f"/subscriptions/{credential['subscription_id']}"
        classic_admins = list(auth_client.classic_administrators.list())

        if len(classic_admins) <= 1:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="No excessive classic administrators",
                    status="pass",
                    severity=self.severity,
                    message=f"Found {len(classic_admins)} classic admin(s). Classic admin model is not over-used.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=scope,
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title=f"{len(classic_admins)} classic administrators found",
                status="fail",
                severity=self.severity,
                message=f"Found {len(classic_admins)} classic subscription administrators. Migrate to Azure RBAC.",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Remove classic administrators and assign RBAC roles instead.",
                remediation_steps=[
                    "Go to Azure Portal > Subscriptions > Access control (IAM)",
                    "Review classic administrators",
                    "Assign equivalent RBAC roles",
                    "Remove classic administrator assignments",
                ],
                resource=scope,
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class CustomRoleRBACCheck(AzureCheck):
    check_id = "azure_custom_role_rbac"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.authorization import AuthorizationManagementClient

        auth_client = AuthorizationManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        scope = f"/subscriptions/{credential['subscription_id']}"
        custom_roles = [
            r for r in auth_client.role_definitions.list(scope=scope)
            if r.role_type == "CustomRole"
        ]

        overly_broad = []
        for role in custom_roles:
            if role.permissions:
                for perm in role.permissions:
                    if perm.actions and "*" in perm.actions:
                        overly_broad.append(role.role_name)
                        break

        if not overly_broad:
            return [
                CheckResult(
                    check_id=self.check_id,
                    title="Custom RBAC roles follow least privilege",
                    status="pass",
                    severity=self.severity,
                    message=f"Checked {len(custom_roles)} custom role(s). None have wildcard (*) permissions.",
                    provider="azure",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource=scope,
                    domain=self.domain,
                    resource_type="Azure",
                )
            ]
        return [
            CheckResult(
                check_id=self.check_id,
                title=f"{len(overly_broad)} custom role(s) with wildcard permissions",
                status="fail",
                severity=self.severity,
                message=f"Custom roles with wildcard (*) actions: {', '.join(overly_broad)}",
                provider="azure",
                nis2_article=self.nis2_article,
                nis2_requirement=self.nis2_requirement,
                remediation="Scope custom role permissions to specific actions instead of wildcard.",
                remediation_steps=[
                    "Review each custom role in Azure Portal > Subscriptions > Access control > Roles",
                    "Replace '*' actions with specific resource provider actions",
                    "Test role assignments after modification",
                ],
                resource=scope,
                domain=self.domain,
                resource_type="Azure",
            )
        ]


class KeyVaultRBACCheck(AzureCheck):
    check_id = "azure_key_vault_rbac"
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
            vault_name = vault.name
            try:
                full_vault = kv_client.vaults.get(rg, vault_name)
                uses_rbac = full_vault.properties.enable_rbac_authorization
            except Exception:
                uses_rbac = False

            if uses_rbac:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Key Vault '{vault_name}' uses RBAC",
                        status="pass",
                        severity=self.severity,
                        message=f"Key Vault '{vault_name}' has RBAC authorization enabled.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=vault.id or vault_name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Key Vault '{vault_name}' does NOT use RBAC",
                        status="fail",
                        severity=self.severity,
                        message=f"Key Vault '{vault_name}' uses access policies instead of RBAC.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable RBAC authorization on Key Vault '{vault_name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Key Vault '{vault_name}' > Access configuration",
                            "Switch 'Permission model' from 'Vault access policy' to 'Azure role-based access control'",
                            "Assign appropriate Key Vault RBAC roles to users/apps",
                        ],
                        resource=vault.id or vault_name,
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


class ManagedIdentityCheck(AzureCheck):
    check_id = "azure_managed_identity"
    severity = "medium"

    def run(self, credential) -> list[CheckResult]:
        from azure.mgmt.compute import ComputeManagementClient

        compute_client = ComputeManagementClient(
            credential=credential["credential"],
            subscription_id=credential["subscription_id"],
        )
        vms = list(compute_client.virtual_machines.list_all())
        results = []

        for vm in vms:
            has_identity = vm.identity is not None and vm.identity.type is not None
            if has_identity:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"VM '{vm.name}' has managed identity",
                        status="pass",
                        severity=self.severity,
                        message=f"VM '{vm.name}' uses managed identity ({vm.identity.type}).",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=vm.id or vm.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"VM '{vm.name}' has no managed identity",
                        status="fail",
                        severity=self.severity,
                        message=f"VM '{vm.name}' does not have a managed identity assigned.",
                        provider="azure",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Assign a managed identity to VM '{vm.name}'.",
                        remediation_steps=[
                            f"Go to Azure Portal > Virtual Machines > '{vm.name}' > Identity",
                            "Enable 'System assigned' managed identity, or",
                            "Add a 'User assigned' managed identity",
                            "Update applications to use managed identity for Azure service access",
                        ],
                        resource=vm.id or vm.name,
                        domain=self.domain,
                        resource_type="Azure",
                    )
                )

        if not results:
            results.append(
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
            )
        return results
