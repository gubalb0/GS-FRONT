"""Endpoints do gestor (RBAC): login, fila completa e mudança de status."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.dependencies import get_repo, require_manager
from app.providers.repository import Repository
from app.schemas.report import LoginIn, LoginOut, ReportOut, StatusUpdate, erro
from app.security import check_password, create_token

router = APIRouter(tags=["gestor"])


@router.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn, settings: Settings = Depends(get_settings)):
    if not check_password(body.senha, settings.manager_password):
        raise HTTPException(401, detail=erro("senha_incorreta", "Senha incorreta."))
    token, exp = create_token(settings.token_secret, settings.token_ttl_minutes)
    return LoginOut(token=token, expira_em=datetime.fromtimestamp(exp, tz=timezone.utc))


@router.get("/manager/reports", response_model=list[ReportOut], dependencies=[Depends(require_manager)])
def fila(repo: Repository = Depends(get_repo)):
    return repo.list_reports()


@router.patch("/manager/reports/{report_id}/status", response_model=ReportOut,
              dependencies=[Depends(require_manager)])
def atualizar_status(report_id: int, body: StatusUpdate, repo: Repository = Depends(get_repo)):
    relato = repo.set_status(report_id, body.status.value, body.nota)
    if not relato:
        raise HTTPException(404, detail=erro("relato_nao_encontrado", "Relato não encontrado."))
    return relato
