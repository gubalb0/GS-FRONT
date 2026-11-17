"""Consulta a publicações oficiais (Gen AI). Recurso opcional: desligado quando GENAI_URL não está configurada."""
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.pipelines.privacy import mask_pii
from app.providers.genai import GenAIClient, GenAIErro, GenAIRespostaInvalida, GenAITimeout
from app.schemas.publicacoes import ConsultaIn, ConsultaOut, SaudeGenAI
from app.schemas.report import erro

router = APIRouter(prefix="/publicacoes", tags=["publicações oficiais (Gen AI)"])


def get_genai(settings: Settings = Depends(get_settings)) -> GenAIClient:
    return GenAIClient(settings.genai_url, settings.genai_timeout_seconds)


@router.get("/saude", response_model=SaudeGenAI)
def saude(genai: GenAIClient = Depends(get_genai)):
    return genai.saude()


@router.post("/perguntar", response_model=ConsultaOut)
def perguntar(body: ConsultaIn, genai: GenAIClient = Depends(get_genai)):
    if not genai.habilitado:
        raise HTTPException(503, detail=erro("genai_desligado",
                            "A consulta a publicações oficiais só funciona na demonstração local do projeto."))
    pergunta, _ = mask_pii(body.pergunta)     # minimização: dado pessoal não sai do Zelo
    try:
        return genai.perguntar(pergunta)
    except GenAITimeout:
        raise HTTPException(504, detail=erro("genai_timeout", "A consulta demorou mais que o esperado. Tente novamente."))
    except GenAIRespostaInvalida:
        raise HTTPException(502, detail=erro("genai_resposta_invalida", "O assistente respondeu em um formato inesperado."))
    except GenAIErro:
        raise HTTPException(503, detail=erro("genai_indisponivel",
                            "O assistente de publicações oficiais está fora do ar agora. Tente mais tarde."))
