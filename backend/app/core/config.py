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

    # Odin SSO — RS256 PEM public key exported from AORDIIENL (set via ODIN_JWT_PUBLIC_KEY env var)
    odin_jwt_public_key: str | None = Field(default=None)
    # Portal gateway shared secret — must match TRAEFIK_INTERNAL_KEY in Odin/Traefik
    internal_key: str | None = Field(default=None)
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

    # Social & Web Discovery
    serper_api_key: str | None = Field(default=None)           # https://serper.dev — 2,500 free queries/mo
    apify_api_token: str | None = Field(default=None)          # https://apify.com — social media scraping (IG/TikTok media)
    facebook_access_token: str | None = Field(default=None)    # Facebook Graph API token (optional)
    facebook_app_id: str | None = Field(default=None)           # Facebook App ID — required for token refresh
    facebook_app_secret: str | None = Field(default=None)       # Facebook App Secret — required for token refresh

    # Evolution API — DEPRECATED, kept for backward compat (use Meta API instead)
    evolution_api_url: str | None = Field(default=None)
    evolution_api_key: str | None = Field(default=None)
    evolution_instance: str | None = Field(default=None)
    whatsapp_owner_phone: str = Field(default='')

    # Meta Cloud API (official WhatsApp Business API)
    meta_wa_phone_number_id: str | None = Field(default=None)  # Phone Number ID from Meta Business Manager
    meta_wa_access_token: str | None = Field(default=None)     # System User permanent token

    # Morning — Israeli payment processor (https://morning.co.il)
    morning_api_key: str | None = Field(default=None)
    morning_api_secret: str | None = Field(default=None)
    morning_plan_id: str | None = Field(default=None)          # recurring plan ID (optional)
    morning_webhook_secret: str | None = Field(default=None)   # HMAC key for webhook verification
    morning_fixed_payment_url: str = Field(default='https://mrng.to/Afe6Dg21q0')  # fallback fixed 39 NIS link
    morning_success_url: str = Field(default='https://tazo-web.com/success')
    morning_cancel_url: str = Field(default='https://tazo-web.com')

    # Hostinger — domain registration & DNS
    hostinger_api_token: str | None = Field(default=None)

    # Server infrastructure
    server_public_ip: str = Field(default='76.13.42.13')

    # VIP intake — Google Sign-In bypass for rate limiting
    google_vip_token_expire_minutes: int = Field(default=60)   # VIP token lifetime in minutes

    # LLM providers
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    xai_api_key: str | None = Field(default=None)
    api_base_url: str = Field(default='https://api.tazo-web.com')
    llm_default_model: str = Field(default='gpt-4o')

    # OTP / delivery
    delivery_mode: str = Field(default='console')   # 'console' | 'whatsapp' | 'sms' | 'voice'
    otp_digits: int = Field(default=4)              # digits in OTP code (4 for voice, 6 for text)
    whatsapp_api_key: str | None = Field(default=None)
    whatsapp_webhook_secret: str | None = Field(default=None)
    whatsapp_verify_token: str = Field(default='tazo-web-verify')
    notification_email: str | None = Field(default=None)
    sms_provider: str | None = Field(default=None)

    # Twilio — voice OTP calls
    twilio_account_sid: str | None = Field(default=None)
    twilio_auth_token: str | None = Field(default=None)
    twilio_api_key_sid: str | None = Field(default=None)
    twilio_api_key_secret: str | None = Field(default=None)
    twilio_from_number: str | None = Field(default=None)  # e.g. +12015551234

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
