"""Zelo API — ponto de entrada FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import repo_for
from app.routers import health, manager, reports
from app.schemas.report import erro

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("zelo")

NOMES_CAMPOS = {"descricao": "Descrição", "bairro": "Bairro", "cep": "CEP", "senha": "Senha",
                "categoria_final": "Tipo de problema", "urgencia_final": "Urgência", "comentario": "Comentário",
                "nota": "Observação", "analise_id": "Análise"}


def _mensagem(e: dict) -> str:
    campo = next((str(p) for p in reversed(e.get("loc", ())) if p not in ("body", "query", "path")), "entrada")
    nome, ctx, tipo = NOMES_CAMPOS.get(campo, campo.capitalize()), e.get("ctx", {}), e.get("type", "")
    if tipo == "string_too_short":
        return f"{nome} precisa ter pelo menos {ctx.get('min_length')} caracteres."
    if tipo == "string_too_long":
        return f"{nome} pode ter no máximo {ctx.get('max_length')} caracteres."
    if tipo == "missing":
        return f"{nome} é obrigatório."
    if tipo == "value_error":
        return str(ctx.get("error") or e.get("msg"))
    return f"{nome} está em um formato inválido."


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    repo = repo_for(settings.database_path)
    if settings.seed_demo_data and repo.count() == 0:
        repo.seed_demo()
        logger.info("Dados de demonstração criados")
    if settings.manager_password == "troque-esta-senha":
        logger.warning("MANAGER_PASSWORD padrão em uso — defina uma senha no .env")
    yield


settings = get_settings()
app = FastAPI(title="Zelo API", version="1.0.0", lifespan=lifespan,
              description="Triagem inteligente de problemas urbanos relatados por cidadãos.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,  # nunca "*"
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)


@app.exception_handler(RequestValidationError)
async def erro_validacao(_: Request, exc: RequestValidationError):
    campos = [_mensagem(e) for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": erro("entrada_invalida", "Alguns dados precisam ser corrigidos.", campos)})


@app.exception_handler(Exception)
async def erro_inesperado(_: Request, exc: Exception):
    logger.exception("Erro inesperado", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": erro("erro_interno", "Algo deu errado do nosso lado. Tente novamente mais tarde.")})


app.include_router(health.router)
app.include_router(reports.router)
app.include_router(manager.router)
