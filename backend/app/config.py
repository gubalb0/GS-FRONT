"""Configuração centralizada. Todos os segredos vêm de variáveis de ambiente / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — qualquer provedor compatível com a API de chat da OpenAI (Groq, OpenAI, Gemini, OpenRouter...)
    llm_provider: str = "mock"  # "openai_compat" usa o LLM real; "mock" usa regras (modo demonstração)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 25.0

    # Segurança
    allowed_origins: str = "http://localhost:8501"
    manager_password: str = "troque-esta-senha"
    token_secret: str = "troque-este-segredo"
    token_ttl_minutes: int = 240

    # Dados
    database_path: str = "data/zelo.db"
    seed_demo_data: bool = True
    enable_external_data: bool = True
    external_timeout_seconds: float = 4.0

    @property
    def origins(self) -> list[str]:
        """Lista de origens CORS. O curinga '*' é descartado de propósito."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip() and o.strip() != "*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
