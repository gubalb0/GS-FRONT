"""Cliente do serviço local do Gen AI. O Zelo nunca fala com o LM Studio: só com este serviço isolado."""
import logging

import httpx
from pydantic import ValidationError

from app.schemas.publicacoes import ConsultaOut, SaudeGenAI

logger = logging.getLogger("zelo.genai")


class GenAIErro(Exception):
    """Serviço do Gen AI fora do ar ou com erro."""


class GenAITimeout(GenAIErro):
    """O modelo demorou além do limite."""


class GenAIRespostaInvalida(GenAIErro):
    """O serviço respondeu fora do contrato."""


class GenAIClient:
    def __init__(self, base_url: str, timeout: float = 200.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def habilitado(self) -> bool:
        return bool(self.base_url)

    def saude(self) -> SaudeGenAI:
        if not self.habilitado:
            return SaudeGenAI(habilitado=False, servico_online=False, modelo_disponivel=False)
        try:
            r = httpx.get(f"{self.base_url}/saude", timeout=3.0)
            r.raise_for_status()
            return SaudeGenAI(habilitado=True, servico_online=True, modelo_disponivel=bool(r.json().get("modelo_disponivel")))
        except (httpx.HTTPError, ValueError):
            return SaudeGenAI(habilitado=True, servico_online=False, modelo_disponivel=False)

    def perguntar(self, pergunta: str) -> ConsultaOut:
        try:
            r = httpx.post(f"{self.base_url}/perguntar", json={"pergunta": pergunta},
                           timeout=httpx.Timeout(self.timeout, connect=5.0))
        except httpx.TimeoutException as exc:
            raise GenAITimeout("timeout") from exc
        except httpx.HTTPError as exc:
            logger.warning("Serviço Gen AI inacessível: %s", type(exc).__name__)
            raise GenAIErro("rede") from exc
        if r.status_code != 200:
            logger.warning("Serviço Gen AI respondeu HTTP %s", r.status_code)
            raise GenAIErro(f"http_{r.status_code}")
        try:
            return ConsultaOut.model_validate(r.json())
        except (ValidationError, ValueError) as exc:
            raise GenAIRespostaInvalida(str(exc)[:200]) from exc
