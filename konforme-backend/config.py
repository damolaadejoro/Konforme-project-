from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DynamoDB (endpoint_url: set for DynamoDB Local / moto server in development)
    dynamodb_table: str = "konforme"
    dynamodb_region: str = "eu-west-1"
    dynamodb_endpoint_url: str = ""
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
    upload_dir: str = "/data/evidence"
    max_upload_size_mb: int = 10
    signup_webhook_url: str = ""

    # Lambda function that runs scans asynchronously (empty = FastAPI BackgroundTasks)
    worker_function_name: str = ""

    # S3 evidence storage (empty bucket = filesystem fallback)
    s3_evidence_bucket: str = ""
    s3_evidence_prefix: str = "evidence/"
    s3_evidence_region: str = "eu-west-1"
    s3_evidence_access_key_id: str = ""
    s3_evidence_secret_access_key: str = ""
    s3_signed_url_expiry: int = 3600

    # S3 reports storage (empty bucket = filesystem fallback)
    s3_reports_bucket: str = ""
    s3_reports_prefix: str = "reports/"
    s3_reports_region: str = "eu-west-1"

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
