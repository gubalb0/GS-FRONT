"""Endpoints do cidadão: analisar, confirmar, acompanhar e avaliar relatos."""
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_llm, get_open_data, get_repo
from app.pipelines.privacy import mask_pii
from app.pipelines.triage import run_triage
from app.providers.llm import LLMError, LLMInvalidResponse, LLMProvider, LLMRateLimit, LLMTimeout
from app.providers.open_data import OpenDataProvider
from app.providers.repository import Repository
from app.schemas.report import (
    AnalysisResponse, FeedbackIn, PublicReport, ReportConfirm, ReportInput, ReportOut, erro,
)

router = APIRouter(prefix="/reports", tags=["relatos"])
logger = logging.getLogger("zelo.reports")


@router.post("/analyze", response_model=AnalysisResponse)
def analisar(entrada: ReportInput, llm: LLMProvider = Depends(get_llm),
             dados: OpenDataProvider = Depends(get_open_data), repo: Repository = Depends(get_repo)):
    """Passo 1: a IA analisa. Nada é registrado como relato ainda — o cidadão precisa confirmar."""
    try:
        resultado = run_triage(entrada, llm, dados)
    except LLMTimeout:
        raise HTTPException(504, detail=erro("ia_timeout", "A análise demorou mais que o esperado. Tente de novo em instantes."))
    except LLMRateLimit:
        raise HTTPException(429, detail=erro("ia_ocupada", "Muita gente usando a assistente agora. Aguarde alguns segundos e tente de novo."))
    except LLMInvalidResponse:
        logger.warning("LLM devolveu saída inválida após novas tentativas")
        raise HTTPException(502, detail=erro("ia_resposta_invalida", "Não conseguimos entender a resposta da IA desta vez. Tente novamente."))
    except LLMError:
        raise HTTPException(503, detail=erro("ia_indisponivel", "Nossa assistente está indisponível agora. Tente novamente em alguns minutos."))

    analise_id = uuid4().hex
    entrada_segura = entrada.model_dump(mode="json")
    entrada_segura["descricao"], _ = mask_pii(entrada.descricao)
    repo.save_analysis(analise_id, entrada_segura, resultado.analise.model_dump(mode="json"))
    return resultado.model_copy(update={"analise_id": analise_id})


@router.post("", response_model=ReportOut, status_code=201)
def confirmar(body: ReportConfirm, repo: Repository = Depends(get_repo)):
    """Passo 2 (human-in-the-loop): o cidadão confirma ou corrige categoria/urgência antes do registro."""
    pendente = repo.pop_analysis(body.analise_id)
    if not pendente:
        raise HTTPException(404, detail=erro("analise_nao_encontrada", "Esta análise expirou ou já foi enviada. Faça a análise novamente."))
    entrada, analise = pendente
    return repo.create_report(entrada, analise, body.categoria_final.value, body.urgencia_final.value)


@router.get("/mine", response_model=list[ReportOut])
def meus_relatos(protocolos: str = Query(..., max_length=1000), repo: Repository = Depends(get_repo)):
    """O protocolo funciona como 'chave' do relato: só quem o tem consegue consultá-lo."""
    lista = [p.strip() for p in protocolos.split(",") if p.strip()][:50]
    return repo.get_by_protocols(lista)


@router.get("/public", response_model=list[PublicReport])
def relatos_publicos(repo: Repository = Depends(get_repo)):
    """Dados anonimizados para o painel da cidade."""
    return repo.list_reports()


@router.patch("/{protocolo}/feedback", response_model=ReportOut)
def avaliar(protocolo: str, body: FeedbackIn, repo: Repository = Depends(get_repo)):
    relato = repo.set_feedback(protocolo, body.util, body.comentario)
    if not relato:
        raise HTTPException(404, detail=erro("relato_nao_encontrado", "Não encontramos esse protocolo."))
    return relato
