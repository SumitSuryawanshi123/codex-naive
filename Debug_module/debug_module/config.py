from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./debugos.db"
    llm_cache_path: Path = Path(".cache/llm_cache.sqlite3")
    openai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("GPT_API_KEY", "OPENAI_API_KEY"))
    openai_model: str = "gpt-4.1-mini"
    enable_llm_reasoning: bool = True
    default_budget: int = 4
    high_threshold: int = 7
    low_threshold: int = 2
    margin_threshold: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
