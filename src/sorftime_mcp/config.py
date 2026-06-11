from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    sorftime_api_key: SecretStr = Field(alias="SORFTIME_API_KEY")
    sorftime_api_base_url: str = Field(
        default="https://standardapi.sorftime.com/api",
        alias="SORFTIME_API_BASE_URL",
    )
    sorftime_api_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        alias="SORFTIME_API_TIMEOUT_SECONDS",
    )
    sorftime_api_max_retries: int = Field(default=3, ge=0, le=10, alias="SORFTIME_API_MAX_RETRIES")
    sorftime_api_retry_base_delay_seconds: float = Field(
        default=2.0,
        gt=0,
        alias="SORFTIME_API_RETRY_BASE_DELAY_SECONDS",
    )
    sorftime_api_retry_max_delay_seconds: float = Field(
        default=15.0,
        gt=0,
        alias="SORFTIME_API_RETRY_MAX_DELAY_SECONDS",
    )
    sorftime_mcp_jwt_secret: SecretStr = Field(alias="SORFTIME_MCP_JWT_SECRET")
    sorftime_mcp_issuer: str = Field(default="sorftime-mcp", alias="SORFTIME_MCP_ISSUER")
    sorftime_mcp_audience: str = Field(
        default="sorftime-mcp-users",
        alias="SORFTIME_MCP_AUDIENCE",
    )
    sorftime_audit_log_path: Path | None = Field(default=None, alias="SORFTIME_AUDIT_LOG_PATH")

    @property
    def api_key(self) -> str:
        return self.sorftime_api_key.get_secret_value()

    @property
    def jwt_secret(self) -> str:
        return self.sorftime_mcp_jwt_secret.get_secret_value()

    @property
    def api_base_url(self) -> str:
        return self.sorftime_api_base_url.rstrip("/")


def load_settings() -> Settings:
    return Settings()
