"""Cliente HTTP da API Zelo. É a ÚNICA camada do front que conhece URLs e códigos HTTP.

Toda falha vira ApiError com uma mensagem pronta para o cidadão (sem detalhes técnicos).
"""
import os
from typing import Any

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MENSAGENS = {
    "offline": "Não conseguimos falar com o serviço agora. Verifique sua internet ou tente de novo em alguns minutos.",
    "timeout": "O serviço demorou mais que o esperado para responder. Tente novamente.",
    "resposta_invalida": "Recebemos uma resposta inesperada do serviço. Tente novamente.",
    "erro_interno": "Algo deu errado do nosso lado. Tente novamente mais tarde.",
}


class ApiError(Exception):
    def __init__(self, codigo: str, mensagem: str, campos: list[str] | None = None, status: int | None = None):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campos, self.status = codigo, mensagem, campos or [], status


def _api_url() -> str:
    url = os.getenv("API_URL")
    if not url:
        try:
            url = st.secrets.get("API_URL")
        except Exception:  # sem secrets.toml
            url = None
    return (url or "http://localhost:8000").rstrip("/")


@st.cache_resource(show_spinner=False)
def _client(base_url: str) -> httpx.Client:
    """Uma conexão reaproveitada entre reruns (cache_resource)."""
    return httpx.Client(base_url=base_url, timeout=httpx.Timeout(45.0, connect=5.0),
                        headers={"User-Agent": "zelo-frontend/1.0"})


def _request(method: str, path: str, *, token: str | None = None, **kwargs) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = _client(_api_url()).request(method, path, headers=headers, **kwargs)
    except httpx.TimeoutException as exc:
        raise ApiError("timeout", MENSAGENS["timeout"]) from exc
    except httpx.HTTPError as exc:
        raise ApiError("offline", MENSAGENS["offline"]) from exc

    try:
        data = resp.json()
    except ValueError:
        data = None

    if resp.status_code >= 400:
        detalhe = data.get("detail") if isinstance(data, dict) else None
        if isinstance(detalhe, dict) and detalhe.get("mensagem"):
            raise ApiError(detalhe.get("codigo", "erro"), detalhe["mensagem"], detalhe.get("campos"), resp.status_code)
        codigo = "erro_interno" if resp.status_code >= 500 else "resposta_invalida"
        raise ApiError(codigo, MENSAGENS[codigo], status=resp.status_code)
    if data is None:
        raise ApiError("resposta_invalida", MENSAGENS["resposta_invalida"])
    return data


def _exige(data: Any, chaves: set[str]) -> dict:
    """Protege a interface contra respostas fora do contrato."""
    if not isinstance(data, dict) or not chaves.issubset(data):
        raise ApiError("resposta_invalida", MENSAGENS["resposta_invalida"])
    return data


def _exige_lista(data: Any) -> list[dict]:
    if not isinstance(data, list):
        raise ApiError("resposta_invalida", MENSAGENS["resposta_invalida"])
    return data


# ------------------------- Endpoints -------------------------
@st.cache_data(ttl=20, show_spinner=False)
def saude() -> dict:
    return _exige(_request("GET", "/health"), {"status", "modo"})


@st.cache_data(ttl=600, show_spinner=False, max_entries=50)
def analisar(descricao: str, bairro: str, cep: str | None, categoria: str | None) -> dict:
    """Cacheado: reenviar exatamente o mesmo relato não gasta outra chamada ao LLM."""
    data = _request("POST", "/reports/analyze",
                    json={"descricao": descricao, "bairro": bairro, "cep": cep, "categoria_sugerida": categoria})
    _exige(data, {"analise_id", "analise", "contexto", "precisa_revisao", "modo"})
    _exige(data["analise"], {"categoria", "urgencia", "orientacoes", "resumo", "orgao_responsavel", "confianca"})
    return data


def confirmar(analise_id: str, categoria: str, urgencia: str) -> dict:
    data = _exige(_request("POST", "/reports", json={"analise_id": analise_id, "categoria_final": categoria,
                                                    "urgencia_final": urgencia}), {"protocolo", "status"})
    analisar.clear()  # a análise foi consumida; um novo envio precisa de nova análise
    relatos_publicos.clear()
    return data


def enviar_feedback(protocolo: str, util: bool, comentario: str | None = None) -> dict:
    return _exige(_request("PATCH", f"/reports/{protocolo}/feedback",
                           json={"util": util, "comentario": comentario}), {"protocolo"})


@st.cache_data(ttl=15, show_spinner=False)
def meus_relatos(protocolos: tuple[str, ...]) -> list[dict]:
    if not protocolos:
        return []
    return _exige_lista(_request("GET", "/reports/mine", params={"protocolos": ",".join(protocolos)}))


@st.cache_data(ttl=60, show_spinner=False)
def relatos_publicos() -> list[dict]:
    return _exige_lista(_request("GET", "/reports/public"))


def login(senha: str) -> dict:
    return _exige(_request("POST", "/auth/login", json={"senha": senha}), {"token"})


@st.cache_data(ttl=15, show_spinner=False)
def relatos_gestor(token: str) -> list[dict]:
    return _exige_lista(_request("GET", "/manager/reports", token=token))


def atualizar_status(token: str, relato_id: int, status: str, nota: str | None) -> dict:
    data = _exige(_request("PATCH", f"/manager/reports/{relato_id}/status", token=token,
                           json={"status": status, "nota": nota or None}), {"status"})
    relatos_gestor.clear()
    relatos_publicos.clear()
    meus_relatos.clear()
    return data
