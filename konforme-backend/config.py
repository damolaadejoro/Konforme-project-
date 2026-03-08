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
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    upload_dir: str = "/data/evidence"
    max_upload_size_mb: int = 10

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
