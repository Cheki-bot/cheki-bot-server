from typing import Annotated

from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str
    emb_model: str
    api_key: SecretStr
    temperature: float
    max_tokens: int
    context_length: int


class ChromaConfig(BaseModel):
    persist_directory: str


class Settings(BaseSettings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # env vars
    llm: LLMConfig
    chroma: ChromaConfig
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
