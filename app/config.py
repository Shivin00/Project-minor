import os

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "sqlite:////tmp/app.db" if os.getenv("VERCEL") else "sqlite:///./data/app.db"


class Settings(BaseSettings):
    app_name: str = "Code-Mixed Hyper-Local Sentiment Analytics"
    app_env: str = "development"
    database_url: str = DEFAULT_DATABASE_URL
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"
    max_text_length: int = 1200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
