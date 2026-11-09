"""Injeção de dependências do FastAPI (facilita trocar implementações nos testes)."""
from functools import lru_cache

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings
from app.providers.llm import LLMProvider, build_llm
from app.providers.open_data import OpenDataProvider
from app.providers.repository import Repository
from app.schemas.report import erro
from app.security import verify_token


@lru_cache
def repo_for(path: str) -> Repository:
    repo = Repository(path)
    repo.init()
    return repo


@lru_cache
def open_data_for(enabled: bool, timeout: float) -> OpenDataProvider:
    return OpenDataProvider(enabled=enabled, timeout=timeout)


def get_repo(settings: Settings = Depends(get_settings)) -> Repository:
    return repo_for(settings.database_path)


def get_llm(settings: Settings = Depends(get_settings)) -> LLMProvider:
    return build_llm(settings)


def get_open_data(settings: Settings = Depends(get_settings)) -> OpenDataProvider:
    return open_data_for(settings.enable_external_data, settings.external_timeout_seconds)


def require_manager(authorization: str | None = Header(default=None),
                    settings: Settings = Depends(get_settings)) -> None:
    if not authorization or not authorization.startswith("Bearer ") \
            or not verify_token(authorization[7:], settings.token_secret):
        raise HTTPException(401, detail=erro("nao_autorizado", "Sua sessão de gestor expirou. Entre novamente."))
