import secrets
import warnings
import os
import logging
from typing import Annotated, Any, Literal
from dotenv import load_dotenv
from mysql.connector.opentelemetry.constants import FIRST_SUPPORTED_VERSION

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
PROJECT_NAME = os.getenv("PROJECT_NAME", "DongoPet")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dongopet")
SECRET_KEY = os.getenv("SECRET_KEY", "")
FIRST_SUPERUSER_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "")

# Log environment variables (mask password)
logger.info("=== DATABASE CONNECTION DEBUG ===")
logger.info(f"POSTGRES_SERVER: {POSTGRES_SERVER}")
logger.info(f"POSTGRES_PORT: {POSTGRES_PORT}")
logger.info(f"POSTGRES_USER: {POSTGRES_USER}")
logger.info(f"POSTGRES_PASSWORD: {'*' * len(str(POSTGRES_PASSWORD)) if POSTGRES_PASSWORD else 'EMPTY'}")
logger.info(f"POSTGRES_DB: {POSTGRES_DB}")
logger.info("=== END DEBUG ===")

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = PROJECT_NAME
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str = POSTGRES_SERVER
    POSTGRES_PORT: int = POSTGRES_PORT
    POSTGRES_USER: str = POSTGRES_USER
    POSTGRES_PASSWORD: str = POSTGRES_PASSWORD
    POSTGRES_DB: str = POSTGRES_DB
    SECRET_KEY: str = SECRET_KEY
    FIRST_SUPERUSER_PASSWORD: str = FIRST_SUPERUSER_PASSWORD

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        logger.info("=== BUILDING DATABASE URI ===")
        logger.info(f"Building URI with - User: {self.POSTGRES_USER}, Host: {self.POSTGRES_SERVER}, Port: {self.POSTGRES_PORT}, DB: {self.POSTGRES_DB}")
        
        # Log each parameter individually
        logger.info(f"scheme: 'postgresql+psycopg'")
        logger.info(f"username: '{self.POSTGRES_USER}' (type: {type(self.POSTGRES_USER)})")
        logger.info(f"password: '{'*' * len(str(self.POSTGRES_PASSWORD)) if self.POSTGRES_PASSWORD else 'EMPTY'}' (type: {type(self.POSTGRES_PASSWORD)})")
        logger.info(f"host: '{self.POSTGRES_SERVER}' (type: {type(self.POSTGRES_SERVER)})")
        logger.info(f"port: {self.POSTGRES_PORT} (type: {type(self.POSTGRES_PORT)})")
        logger.info(f"path: '{self.POSTGRES_DB}' (type: {type(self.POSTGRES_DB)})")
        
        try:
            # Try building the URL manually first
            manual_url = f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            logger.info(f"Manual URL would be: {manual_url.replace(self.POSTGRES_PASSWORD, '*' * len(self.POSTGRES_PASSWORD))}")
            
            uri = MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
            # Log URI with masked password
            uri_str = str(uri)
            masked_uri = uri_str.replace(self.POSTGRES_PASSWORD, "*" * len(self.POSTGRES_PASSWORD)) if self.POSTGRES_PASSWORD else uri_str
            logger.info(f"Successfully built URI: {masked_uri}")
            return uri
        except Exception as e:
            logger.error(f"Failed to build database URI: {e}")
            logger.error(f"Exception type: {type(e)}")
            # Try alternative approach
            try:
                logger.info("Trying alternative PostgresDsn approach...")
                from pydantic import PostgresDsn
                manual_url = f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                uri = PostgresDsn(manual_url)
                logger.info(f"Alternative approach succeeded: {str(uri).replace(self.POSTGRES_PASSWORD, '*' * len(self.POSTGRES_PASSWORD))}")
                return uri
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {e2}")
                raise e

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
