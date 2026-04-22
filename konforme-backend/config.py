from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./konforme.db"
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    konforme_aws_account_id: str = ""
    encryption_key: str = ""
    rate_limit_per_minute: int = 60
    environment: str = "development"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    cookie_domain: str = ""
    cookie_secure: bool = True
    cookie_samesite: str = "lax"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    upload_dir: str = "/data/evidence"
    max_upload_size_mb: int = 10
    signup_webhook_url: str = ""

    # S3 evidence storage (empty bucket = filesystem fallback)
    s3_evidence_bucket: str = ""
    s3_evidence_prefix: str = "evidence/"
    s3_evidence_region: str = "eu-west-1"
    s3_evidence_access_key_id: str = ""
    s3_evidence_secret_access_key: str = ""
    s3_signed_url_expiry: int = 3600

    # Email provider: "resend" or "ses"
    email_provider: str = "resend"
    resend_api_key: str = ""

    # AWS SES email settings
    aws_ses_access_key_id: str = ""
    aws_ses_secret_access_key: str = ""
    aws_ses_region: str = "eu-west-1"
    sender_email: str = "noreply@konforme.io"
    frontend_base_url: str = "http://localhost:5173"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
