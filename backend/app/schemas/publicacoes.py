"""Contrato com o serviço do Gen AI (integracao_citizentech, versão 1.x)."""
import re

from pydantic import BaseModel, Field, field_validator

STATUS_GENAI = ("respondida", "parcial", "ambigua", "insuficiente", "fora_do_escopo", "indisponivel")


class ConsultaIn(BaseModel):
    pergunta: str = Field(min_length=10, max_length=500)

    @field_validator("pergunta", mode="before")
    @classmethod
    def _limpar(cls, v):
        return re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v


class FontePublicacao(BaseModel):
    referencia: str | None = None
    tipo_documento: str | None = None
    numero_documento: str | None = None
    edicao: int | str | None = None
    data_edicao: str | None = None
    secao: str | None = None
    trechos: list[str] = Field(default_factory=list)


class ConsultaOut(BaseModel):
    versao_contrato: str
    versao_politica: str
    status: str
    rotulo_status: str
    resposta: str
    aviso: str | None = None
    fontes: list[FontePublicacao] = Field(default_factory=list)
    erro_tecnico: str | None = None
    latencia_s: float | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, v):
        if v not in STATUS_GENAI:
            raise ValueError(f"status desconhecido: {v}")
        return v

    @field_validator("versao_contrato")
    @classmethod
    def _versao(cls, v):
        if not v.startswith("1."):
            raise ValueError(f"versão de contrato incompatível: {v}")
        return v


class SaudeGenAI(BaseModel):
    habilitado: bool          # GENAI_URL configurada neste servidor
    servico_online: bool      # o serviço do Gen AI respondeu
    modelo_disponivel: bool   # o LM Studio está com o modelo carregado
