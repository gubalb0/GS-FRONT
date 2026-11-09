"""Dados abertos públicos (sem chave): ViaCEP (endereço) e Open-Meteo (previsão de chuva).

Falhas aqui NUNCA derrubam a análise: o contexto externo é um bônus.
"""
import logging
import time
from typing import Any, Callable

import httpx

logger = logging.getLogger("zelo.open_data")


class OpenDataProvider:
    def __init__(self, enabled: bool = True, timeout: float = 4.0, ttl_seconds: int = 1800):
        self.enabled = enabled
        self.timeout = timeout
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def _cached(self, chave: str, fn: Callable[[], Any]) -> Any:
        agora = time.time()
        if chave in self._cache and agora - self._cache[chave][0] < self.ttl:
            return self._cache[chave][1]
        valor = fn()
        if valor is not None:
            self._cache[chave] = (agora, valor)
        return valor

    def _get_json(self, url: str, params: dict | None = None) -> Any | None:
        if not self.enabled:
            return None
        try:
            resp = httpx.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Dado externo indisponível (%s): %s", url, type(exc).__name__)
            return None

    def endereco_por_cep(self, cep: str) -> dict | None:
        def buscar():
            dados = self._get_json(f"https://viacep.com.br/ws/{cep}/json/")
            if not isinstance(dados, dict) or dados.get("erro"):
                return None
            return {k: dados.get(k) for k in ("logradouro", "bairro", "localidade", "uf")}

        return self._cached(f"cep:{cep}", buscar)

    def chuva_prevista_mm(self, cidade: str) -> float | None:
        """Maior acumulado diário de chuva previsto para hoje/amanhã (mm)."""

        def buscar():
            geo = self._get_json(
                "https://geocoding-api.open-meteo.com/v1/search",
                {"name": cidade, "count": 1, "language": "pt", "countryCode": "BR"},
            )
            resultados = (geo or {}).get("results") or []
            if not resultados:
                return None
            lat, lon = resultados[0]["latitude"], resultados[0]["longitude"]
            prev = self._get_json(
                "https://api.open-meteo.com/v1/forecast",
                {"latitude": lat, "longitude": lon, "daily": "precipitation_sum",
                 "forecast_days": 2, "timezone": "America/Sao_Paulo"},
            )
            valores = [v for v in ((prev or {}).get("daily") or {}).get("precipitation_sum", []) if v is not None]
            return max(valores) if valores else None

        return self._cached(f"chuva:{cidade.lower()}", buscar)
