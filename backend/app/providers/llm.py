"""Acesso ao LLM. O front-end nunca chama o provedor: só este módulo conhece a chave."""
import json
import logging
import re
import time
from typing import Protocol

import httpx

from app.config import Settings

logger = logging.getLogger("zelo.llm")


class LLMError(Exception):
    """IA indisponível (erro HTTP, credencial, cota...)."""


class LLMTimeout(LLMError):
    """IA demorou além do limite."""


class LLMRateLimit(LLMError):
    """Limite de requisições do provedor atingido (HTTP 429)."""


class LLMInvalidResponse(LLMError):
    """IA respondeu algo que não segue o contrato Pydantic."""


class LLMProvider(Protocol):
    modo: str

    def complete(self, messages: list[dict]) -> str: ...


class OpenAICompatibleLLM:
    """Funciona com Groq, OpenAI, Gemini (endpoint /openai), OpenRouter etc."""

    modo = "ia"

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        for tentativa in range(2):
            try:
                resp = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=self.timeout,
                )
            except httpx.TimeoutException as exc:
                logger.warning("Timeout ao chamar o LLM")
                raise LLMTimeout("timeout") from exc
            except httpx.HTTPError as exc:
                logger.warning("Falha de rede ao chamar o LLM: %s", type(exc).__name__)
                raise LLMError("rede") from exc
            if resp.status_code != 429:
                break
            # Limite do plano gratuito: espera o tempo sugerido pelo provedor (máx. 10 s) e tenta uma vez.
            espera = _segundos_retry_after(resp.headers.get("retry-after"))
            logger.warning("LLM respondeu HTTP 429; nova tentativa em %.1f s", espera)
            if tentativa == 0:
                time.sleep(espera)
        if resp.status_code == 429:
            raise LLMRateLimit("http_429")

        if resp.status_code != 200:
            # Loga só o status: o corpo pode conter detalhes da conta.
            logger.warning("LLM respondeu HTTP %s", resp.status_code)
            raise LLMError(f"http_{resp.status_code}")
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMInvalidResponse("formato inesperado") from exc


def _segundos_retry_after(valor: str | None) -> float:
    try:
        return min(max(float(valor), 1.0), 10.0)
    except (TypeError, ValueError):
        return 5.0


# ---------------- Modo demonstração (sem chave) ----------------
_REGRAS = [
    ("alagamento", ["alag", "enchente", "inund", "ilhad", "transbord", "água subindo", "agua subindo"]),
    ("arvore_risco", ["árvore", "arvore", "galho", "tronco"]),
    ("iluminacao_publica", ["poste", "lâmpada", "lampada", "iluminação", "iluminacao", "luz apagada", "escuro"]),
    ("buraco_via", ["buraco", "cratera", "asfalto", "pavimento"]),
    ("agua_esgoto", ["esgoto", "vazamento", "bueiro", "cano", "falta de água", "falta d'água"]),
    ("lixo_entulho", ["lixo", "entulho", "descarte", "caçamba", "cacamba", "sujeira", "rato"]),
    ("calcada_acessibilidade", ["calçada", "calcada", "rampa", "cadeirante", "acessib"]),
    ("sinalizacao_transito", ["semáforo", "semaforo", "farol", "placa", "faixa de pedestre", "sinaliza"]),
]
_CRITICOS = ["fio caído", "fio caido", "fio solto", "choque", "ilhad", "desab", "caiu sobre", "caindo sobre", "risco de vida"]
_ALTOS = ["acidente", "moto", "escola", "hospital", "cratera", "perigo", "perigos", "criança", "crianca", "idoso", "noite toda"]

ORGAOS = {
    "buraco_via": "Subprefeitura / Secretaria de Obras (manutenção viária)",
    "iluminacao_publica": "Serviço municipal de iluminação pública",
    "lixo_entulho": "Serviço municipal de limpeza urbana",
    "alagamento": "Defesa Civil municipal (199)",
    "arvore_risco": "Defesa Civil (199) e manejo arbóreo da subprefeitura",
    "calcada_acessibilidade": "Subprefeitura – fiscalização de calçadas",
    "sinalizacao_transito": "Órgão municipal de trânsito",
    "agua_esgoto": "Companhia de saneamento do município",
    "outro": "Central de atendimento da prefeitura (156)",
}

_ORIENTACOES = {
    "buraco_via": ["Se puder, sinalize o local com um objeto visível, sem ficar na pista.", "Tire uma foto de longe para registrar o tamanho do buraco."],
    "iluminacao_publica": ["Anote o número do poste (fica numa plaqueta no próprio poste).", "Evite passar sozinho pelo trecho escuro à noite até o reparo."],
    "lixo_entulho": ["Não mexa no material: pode haver objetos cortantes ou animais.", "Registre o local e o horário em que o descarte apareceu."],
    "alagamento": ["Não entre na água: ela pode esconder bueiros abertos e fios.", "Desligue a energia da casa se a água estiver entrando."],
    "arvore_risco": ["Mantenha distância da árvore e não estacione embaixo dela.", "Se houver fios encostando nos galhos, avise também a distribuidora de energia."],
    "calcada_acessibilidade": ["Indique se o problema impede a passagem de cadeira de rodas ou carrinho.", "Registre uma foto mostrando a largura livre da calçada."],
    "sinalizacao_transito": ["Atravesse com atenção redobrada enquanto a sinalização estiver com defeito.", "Informe o cruzamento exato (nome das duas ruas)."],
    "agua_esgoto": ["Evite contato com a água ou o esgoto vazando.", "Informe se o vazamento é de água limpa ou de esgoto."],
    "outro": ["Descreva o local com um ponto de referência.", "Acompanhe o andamento pelo protocolo."],
}


class MockLLM:
    """Classificador por palavras-chave. Mantém o app funcionando sem chave de API e nos testes."""

    modo = "demonstracao"

    def complete(self, messages: list[dict]) -> str:
        conteudo = next((m["content"] for m in messages if m["role"] == "user"), "")
        match = re.search(r"\{.*\}", conteudo, re.S)
        try:
            dados = json.loads(match.group(0)) if match else {}
        except ValueError:
            dados = {}
        texto = str(dados.get("relato", conteudo)).lower()

        categoria = dados.get("categoria_sugerida") or "outro"
        pontos = 0
        for cat, palavras in _REGRAS:
            if any(p in texto for p in palavras):
                categoria, pontos = cat, pontos + 1
                break
        if any(p in texto for p in _CRITICOS):
            urgencia = "critica"
        elif any(p in texto for p in _ALTOS):
            urgencia = "alta"
        elif categoria in ("buraco_via", "iluminacao_publica", "arvore_risco", "alagamento", "sinalizacao_transito", "agua_esgoto"):
            urgencia = "media"
        else:
            urgencia = "baixa"

        resposta = {
            "categoria": categoria,
            "urgencia": urgencia,
            "orgao_responsavel": ORGAOS[categoria],
            "resumo": f"Relato de {categoria.replace('_', ' ')} no bairro {dados.get('bairro', 'informado')}.",
            "orientacoes": _ORIENTACOES[categoria],
            "sinais_de_risco": [p for p in _CRITICOS + _ALTOS if p in texto][:3],
            "confianca": 0.7 if pontos else 0.4,
            "justificativa": "Classificação por palavras-chave (modo demonstração, sem IA externa).",
        }
        return json.dumps(resposta, ensure_ascii=False)


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider.lower() != "mock" and settings.llm_api_key:
        return OpenAICompatibleLLM(
            settings.llm_api_key, settings.llm_base_url, settings.llm_model, settings.llm_timeout_seconds
        )
    return MockLLM()
