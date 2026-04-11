from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'LocalBiz AutoSite Platform'
    environment: str = Field(default='development')
    api_v1_prefix: str = '/api/v1'
    backend_host: str = '0.0.0.0'
    backend_port: int = 8000

    # Database
    use_postgres: bool = Field(default=True)
    database_url: str | None = Field(default=None)
    postgres_host: str = Field(default='localhost')
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default='localbiz')
    postgres_user: str = Field(default='localbiz')
    postgres_password: str = Field(default='localbiz')

    # Frontends
    frontend_admin_url: str = 'http://localhost:5173'
    frontend_customer_url: str = 'http://localhost:5174'
    frontend_public_url: str = 'http://localhost:5175'

    # Dev auth + JWT skeleton
    admin_dev_token: str = 'dev-admin-token'
    jwt_secret_key: str = Field(default='change-me-in-production')
    jwt_algorithm: str = Field(default='HS256')
    jwt_expire_minutes: int = Field(default=720)
    admin_seed_email: str = Field(default='ar.2110@gmail.com')
    admin_seed_name: str = Field(default='Ariel')
    allowed_admin_email_domain: str | None = None

    # Google auth skeleton
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_oauth_redirect_url: str = 'http://localhost:8000/api/v1/auth/google/callback'
    # Comma-separated list of emails allowed to log in as admin. Empty = anyone with Google account.
    allowed_admin_emails: str = Field(default='ar.2110@gmail.com')

    # Google Places API for business enrichment
    google_places_api_key: str | None = Field(default=None)

    # LLM providers
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    xai_api_key: str | None = Field(default=None)
    api_base_url: str = Field(default='https://api.sitenest.site')
    llm_default_model: str = Field(default='gpt-4o')

    # OTP / delivery
    delivery_mode: str = Field(default='console')   # 'console' | 'whatsapp' | 'sms'
    whatsapp_api_key: str | None = Field(default=None)
    whatsapp_webhook_secret: str | None = Field(default=None)
    whatsapp_verify_token: str = Field(default='sitenest-verify')
    notification_email: str | None = Field(default=None)
    sms_provider: str | None = Field(default=None)

    # Rate limiting / anti-abuse
    public_challenge_window_minutes: int = Field(default=15)
    public_challenge_max_per_window: int = Field(default=5)
    customer_login_window_minutes: int = Field(default=15)
    customer_login_max_failures: int = Field(default=8)

    # Static output
    static_output_dir: str = 'app/static_sites'

    # App behavior
    default_city: str = 'Tel Aviv-Yafo'
    default_radius_km: int = 8
    auto_create_tables: bool = Field(default=False)
    auto_seed_demo_data: bool = Field(default=False)

    @property
    def postgres_database_url(self) -> str:
        return (
            f'postgresql+psycopg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.use_postgres:
            return self.postgres_database_url
        return 'sqlite:///./localbiz.db'

    @model_validator(mode='after')
    def _validate_production_secrets(self) -> 'Settings':
        if self.environment == 'production':
            if self.jwt_secret_key == 'change-me-in-production':
                raise ValueError(
                    'JWT_SECRET_KEY must be set to a strong random value in production. '
                    'Set the JWT_SECRET_KEY environment variable.'
                )
            if self.admin_dev_token == 'dev-admin-token':
                raise ValueError(
                    'ADMIN_DEV_TOKEN must be changed in production. '
                    'Disable or rotate it via the ADMIN_DEV_TOKEN environment variable.'
                )
        return self


settings = Settings()
