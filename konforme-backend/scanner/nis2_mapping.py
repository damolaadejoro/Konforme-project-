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
}
