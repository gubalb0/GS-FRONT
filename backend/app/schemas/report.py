"""Modelos Pydantic de entrada e saída da API Zelo."""
import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Categoria(str, Enum):
    buraco_via = "buraco_via"
    iluminacao_publica = "iluminacao_publica"
    lixo_entulho = "lixo_entulho"
    alagamento = "alagamento"
    arvore_risco = "arvore_risco"
    calcada_acessibilidade = "calcada_acessibilidade"
    sinalizacao_transito = "sinalizacao_transito"
    agua_esgoto = "agua_esgoto"
    outro = "outro"


class Urgencia(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"
    critica = "critica"


URGENCIA_ORDEM = {"baixa": 0, "media": 1, "alta": 2, "critica": 3}


class Status(str, Enum):
    recebido = "recebido"
    em_analise = "em_analise"
    encaminhado = "encaminhado"
    resolvido = "resolvido"
    recusado = "recusado"


# ---------- Entrada do cidadão ----------
class ReportInput(BaseModel):
    descricao: str = Field(..., min_length=20, max_length=1500, description="Relato do problema em linguagem livre")
    bairro: str = Field(..., min_length=2, max_length=80)
    cep: str | None = Field(default=None, description="CEP com 8 dígitos (opcional)")
    categoria_sugerida: Categoria | None = None

    @field_validator("descricao", "bairro", mode="before")
    @classmethod
    def _limpar(cls, v):
        return re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v

    @field_validator("cep", mode="before")
    @classmethod
    def _cep(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        digitos = re.sub(r"\D", "", str(v))
        if len(digitos) != 8:
            raise ValueError("O CEP deve ter 8 números (ex.: 06010-000).")
        return digitos


# ---------- Saída estruturada do LLM ----------
class TriageResult(BaseModel):
    """Contrato que o LLM é obrigado a seguir (validado; se falhar, há nova tentativa)."""

    categoria: Categoria = Field(description="Categoria do problema urbano")
    urgencia: Urgencia = Field(description="Nível de urgência: baixa, media, alta ou critica")
    orgao_responsavel: str = Field(min_length=3, max_length=160, description="Órgão público mais indicado")
    resumo: str = Field(min_length=10, max_length=400, description="Resumo do problema em uma frase simples")
    orientacoes: list[str] = Field(min_length=1, max_length=5, description="Passos práticos e seguros para o cidadão")
    sinais_de_risco: list[str] = Field(default_factory=list, max_length=5, description="Riscos percebidos no relato")
    confianca: float = Field(ge=0, le=1, description="Confiança da classificação, de 0 a 1")
    justificativa: str = Field(min_length=5, max_length=600, description="Por que essa categoria e urgência")


class ContextoExterno(BaseModel):
    endereco: str | None = None
    cidade: str | None = None
    uf: str | None = None
    chuva_prevista_mm: float | None = None
    alerta_chuva: bool = False
    fontes: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    analise_id: str = ""
    analise: TriageResult
    contexto: ContextoExterno
    precisa_revisao: bool
    modo: str  # "ia" ou "demonstracao"
    dados_pessoais_removidos: bool


# ---------- Confirmação (human-in-the-loop) ----------
class ReportConfirm(BaseModel):
    analise_id: str = Field(min_length=8, max_length=64, pattern=r"^[a-f0-9]+$")
    categoria_final: Categoria
    urgencia_final: Urgencia


class ReportOut(BaseModel):
    id: int
    protocolo: str
    criado_em: datetime
    atualizado_em: datetime
    descricao: str
    bairro: str
    cep: str | None = None
    categoria: Categoria
    urgencia: Urgencia
    categoria_ia: Categoria
    urgencia_ia: Urgencia
    corrigido_pelo_cidadao: bool
    orgao_responsavel: str
    resumo: str
    orientacoes: list[str]
    status: Status
    nota_gestor: str | None = None
    feedback_util: bool | None = None
    feedback_comentario: str | None = None
    demo: bool = False


class PublicReport(BaseModel):
    """Versão anonimizada para o painel público: sem descrição, CEP ou protocolo."""

    categoria: Categoria
    urgencia: Urgencia
    status: Status
    bairro: str
    criado_em: datetime
    corrigido_pelo_cidadao: bool
    feedback_util: bool | None = None
    demo: bool = False


class FeedbackIn(BaseModel):
    util: bool
    comentario: str | None = Field(default=None, max_length=300)


class StatusUpdate(BaseModel):
    status: Status
    nota: str | None = Field(default=None, max_length=300)


class LoginIn(BaseModel):
    senha: str = Field(min_length=1, max_length=128)


class LoginOut(BaseModel):
    token: str
    expira_em: datetime


def erro(codigo: str, mensagem: str, campos: list | None = None) -> dict:
    """Formato único de erro devolvido ao front: sem stack trace, com mensagem para o cidadão."""
    corpo = {"codigo": codigo, "mensagem": mensagem}
    if campos:
        corpo["campos"] = campos
    return corpo
