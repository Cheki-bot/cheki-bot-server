from typing import Annotated

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class LLMConfig(BaseModel):
    api_key: str


class Settings(BaseSettings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # env vars
    llm: LLMConfig
    allow_origins: Annotated[list[str], NoDecode]

    # model configurations
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    @field_validator("allow_origins", mode="before")
    @classmethod
    def decode_allow_origins(cls, value: str) -> list[str]:
        return [origin.strip() for origin in value.split(",")]
