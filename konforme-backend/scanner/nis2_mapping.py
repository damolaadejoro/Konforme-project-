NIS2_MAPPING: dict[str, dict[str, str]] = {
    "cloudtrail_enabled": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Incident handling — audit logging must be enabled",
        "domain": "Logging & Monitoring",
    },
    "cloudtrail_log_validation": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Incident handling — log integrity validation",
        "domain": "Logging & Monitoring",
    },
    "root_mfa": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Multi-factor authentication for root account",
        "domain": "Identity & Access",
    },
    "no_root_access_keys": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Root account should not have access keys",
        "domain": "Identity & Access",
    },
    "old_access_keys": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Access keys should be rotated regularly",
        "domain": "Identity & Access",
    },
    "mfa_users": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "All IAM users with console access should have MFA",
        "domain": "Identity & Access",
    },
    "s3_public_access": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "S3 buckets should block public access",
        "domain": "Data Protection",
    },
    "s3_encryption": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "S3 buckets should have encryption enabled",
        "domain": "Data Protection",
    },
    "s3_versioning": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "S3 buckets should have versioning for backup/recovery",
        "domain": "Data Protection",
    },
    "guardduty_enabled": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Threat detection service must be active",
        "domain": "Threat Detection",
    },
    "security_hub_enabled": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Centralized security findings aggregation",
        "domain": "Threat Detection",
    },
    "security_groups": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "Security groups should not allow unrestricted ingress",
        "domain": "Network Security",
    },
    "vpc_flow_logs": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "VPC flow logs must be enabled for network monitoring",
        "domain": "Network Security",
    },
    "kms_rotation": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "KMS keys should have automatic rotation enabled",
        "domain": "Encryption",
    },
    "ebs_encryption": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "EBS default encryption should be enabled",
        "domain": "Encryption",
    },
    # Art 21(2)(b) — Incident reporting
    "sns_alerts": {
        "article": "Art 21(2)(b)",
        "article_title": "Incident Reporting",
        "requirement": "Automated alerting and notification channels for incident reporting",
        "domain": "Incident Response",
    },
    # Art 21(2)(c) — Business continuity
    "rds_backup": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "Database backup retention, Multi-AZ, and encryption for continuity",
        "domain": "Business Continuity",
    },
    "backup_plan": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "Automated backup plans for critical resource recovery",
        "domain": "Business Continuity",
    },
    # Art 21(2)(e) — Network security
    "nacl_rules": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "Network ACLs should not allow unrestricted inbound traffic",
        "domain": "Network Security",
    },
    "waf_enabled": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "Web Application Firewall should protect internet-facing applications",
        "domain": "Network Security",
    },
    # Art 21(2)(f) — Security testing & vulnerability assessment
    "inspector_enabled": {
        "article": "Art 21(2)(f)",
        "article_title": "Security Testing",
        "requirement": "Automated vulnerability scanning for infrastructure and applications",
        "domain": "Security Testing",
    },
    "config_enabled": {
        "article": "Art 21(2)(f)",
        "article_title": "Security Testing",
        "requirement": "Configuration compliance monitoring and change tracking",
        "domain": "Security Testing",
    },
    # Art 21(2)(h) — Cryptography
    "acm_certificates": {
        "article": "Art 21(2)(h)",
        "article_title": "Cryptography",
        "requirement": "TLS certificates should be valid and not expired",
        "domain": "Cryptography",
    },
    "elb_tls": {
        "article": "Art 21(2)(h)",
        "article_title": "Cryptography",
        "requirement": "Load balancers should enforce HTTPS/TLS with modern security policies",
        "domain": "Cryptography",
    },
    # Art 21(2)(j) — Supply chain security
    "ecr_scanning": {
        "article": "Art 21(2)(j)",
        "article_title": "Supply Chain Security",
        "requirement": "Container image scanning for supply chain vulnerability detection",
        "domain": "Supply Chain",
    },
    # --- Azure checks ---
    # Art 21(2)(i) — Access Control (5 checks)
    "azure_mfa_enforced": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Multi-factor authentication must be enforced for all users",
        "domain": "Identity & Access",
    },
    "azure_no_classic_admins": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Classic subscription administrators should not be used",
        "domain": "Identity & Access",
    },
    "azure_custom_role_rbac": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Custom RBAC roles should limit excessive permissions",
        "domain": "Identity & Access",
    },
    "azure_key_vault_rbac": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Key Vault should use RBAC authorization",
        "domain": "Identity & Access",
    },
    "azure_managed_identity": {
        "article": "Art 21(2)(i)",
        "article_title": "Authentication & Access Control",
        "requirement": "Resources should use managed identities instead of service principals with secrets",
        "domain": "Identity & Access",
    },
    # Art 21(2)(d) / Art 21(2)(h) — Encryption (4 checks)
    "azure_storage_encryption": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "Storage accounts should use customer-managed encryption keys",
        "domain": "Encryption",
    },
    "azure_disk_encryption": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "Virtual machine disks should be encrypted",
        "domain": "Encryption",
    },
    "azure_sql_tde": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "SQL databases should have transparent data encryption enabled",
        "domain": "Encryption",
    },
    "azure_key_vault_expiry": {
        "article": "Art 21(2)(h)",
        "article_title": "Cryptography",
        "requirement": "Key Vault keys and secrets should have expiration dates set",
        "domain": "Cryptography",
    },
    # Art 21(2)(e) — Network Security (4 checks)
    "azure_nsg_unrestricted": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "Network security groups should not allow unrestricted inbound access",
        "domain": "Network Security",
    },
    "azure_sql_firewall": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "SQL servers should not allow unrestricted network access",
        "domain": "Network Security",
    },
    "azure_storage_public_access": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "Storage accounts should restrict public network access",
        "domain": "Network Security",
    },
    "azure_app_service_https": {
        "article": "Art 21(2)(e)",
        "article_title": "Network Security",
        "requirement": "App Service should enforce HTTPS",
        "domain": "Network Security",
    },
    # Art 21(2)(a) — Logging & Monitoring (4 checks)
    "azure_activity_log": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Azure Activity Log should be collected and monitored",
        "domain": "Logging & Monitoring",
    },
    "azure_diagnostic_settings": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Resources should have diagnostic settings configured",
        "domain": "Logging & Monitoring",
    },
    "azure_security_center": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Microsoft Defender for Cloud should be enabled",
        "domain": "Threat Detection",
    },
    "azure_log_analytics": {
        "article": "Art 21(2)(a)",
        "article_title": "Monitoring & Incident Response",
        "requirement": "Log Analytics workspace should be configured for centralized logging",
        "domain": "Logging & Monitoring",
    },
    # Art 21(2)(d) — Data Protection (4 checks)
    "azure_storage_secure_transfer": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "Storage accounts should require secure transfer (HTTPS)",
        "domain": "Data Protection",
    },
    "azure_sql_auditing": {
        "article": "Art 21(2)(d)",
        "article_title": "Data Protection",
        "requirement": "SQL server auditing should be enabled",
        "domain": "Data Protection",
    },
    "azure_sql_threat_detection": {
        "article": "Art 21(2)(f)",
        "article_title": "Security Testing",
        "requirement": "SQL advanced threat protection should be enabled",
        "domain": "Security Testing",
    },
    "azure_storage_soft_delete": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "Storage accounts should have soft delete enabled for data recovery",
        "domain": "Data Protection",
    },
    # Art 21(2)(c) / Art 21(2)(b) — Incident Response & Business Continuity (4 checks)
    "azure_backup_enabled": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "Virtual machines should have Azure Backup enabled",
        "domain": "Business Continuity",
    },
    "azure_sql_geo_replication": {
        "article": "Art 21(2)(c)",
        "article_title": "Business Continuity",
        "requirement": "SQL databases should have geo-replication configured",
        "domain": "Business Continuity",
    },
    "azure_alert_rules": {
        "article": "Art 21(2)(b)",
        "article_title": "Incident Reporting",
        "requirement": "Alert rules should be configured for incident detection and response",
        "domain": "Incident Response",
    },
    "azure_action_groups": {
        "article": "Art 21(2)(b)",
        "article_title": "Incident Reporting",
        "requirement": "Action groups should be configured for incident notification",
        "domain": "Incident Response",
    },
}
