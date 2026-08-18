from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), env_file_encoding="utf-8", extra="ignore")

    adt_database_url: str = ""
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3.2"
    upload_dir: str = "./data/uploads"
    max_upload_bytes: int = 20 * 1024 * 1024
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    @property
    def use_postgres(self) -> bool:
        return self.adt_database_url.startswith("postgresql")

    @property
    def use_neo4j(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_user and self.neo4j_password)


settings = Settings()
