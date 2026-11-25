from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenRouter / OpenAI Configuration
    openai_api_key: str
    openai_model: str
    openai_embedding_model: str

    # Neo4j Configuration
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Qdrant Configuration
    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str
    vector_size: int

    # Application Settings
    app_host: str
    app_port: int
    debug: bool

    # File Upload
    max_file_size: int
    upload_dir: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()