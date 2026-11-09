import os
import sys
from pathlib import Path

# Configuração isolada para os testes (antes de importar o app)
os.environ.update({
    "LLM_PROVIDER": "mock",
    "DATABASE_PATH": ":memory:",
    "SEED_DEMO_DATA": "false",
    "ENABLE_EXTERNAL_DATA": "false",
    "MANAGER_PASSWORD": "senha-teste",
    "TOKEN_SECRET": "segredo-teste",
    "ALLOWED_ORIGINS": "http://localhost:8501",
})
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class FakeOpenData:
    """Dados externos controlados (sem rede)."""

    def __init__(self, chuva=None, endereco=None):
        self.chuva, self.endereco = chuva, endereco

    def endereco_por_cep(self, cep):
        return self.endereco

    def chuva_prevista_mm(self, cidade):
        return self.chuva


class FakeLLM:
    """LLM programável: devolve as respostas da lista em sequência e guarda as mensagens recebidas."""

    modo = "ia"

    def __init__(self, respostas=None, erro=None):
        self.respostas, self.erro, self.chamadas = list(respostas or []), erro, []

    def complete(self, messages):
        self.chamadas.append(messages)
        if self.erro:
            raise self.erro
        return self.respostas.pop(0)
