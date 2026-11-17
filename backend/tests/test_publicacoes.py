"""Integração com o Gen AI (consulta ao Diário Oficial do DF), sem o serviço real."""
import httpx
import pytest

from app.main import app
from app.providers.genai import GenAIClient, GenAIErro, GenAIRespostaInvalida, GenAITimeout
from app.routers.publicacoes import get_genai
from app.schemas.publicacoes import ConsultaOut, SaudeGenAI

PERGUNTA = {"pergunta": "Qual é o serviço de alimentação hospitalar contratado em Ceilândia?"}
RESPOSTA = {
    "versao_contrato": "1.0", "versao_politica": "fail-closed-4.4.4d1-cand", "status": "respondida",
    "rotulo_status": "Resposta encontrada", "resposta": "Fornecimento ininterrupto de alimentação hospitalar.",
    "aviso": None, "erro_tecnico": None, "latencia_s": 14.2,
    "fontes": [{"referencia": None, "tipo_documento": "Extrato", "numero_documento": "CONTRATO nº 1025/2024",
                "edicao": 5, "data_edicao": "2025-01-08", "secao": "Seção III",
                "trechos": ["FORNECIMENTO ININTERRUPTO DE ALIMENTAÇÃO HOSPITALAR"]}],
}


class GenAIFalso:
    def __init__(self, resposta=None, erro=None, habilitado=True):
        self.resposta, self.erro, self.habilitado, self.recebidas = resposta, erro, habilitado, []

    def saude(self):
        return SaudeGenAI(habilitado=self.habilitado, servico_online=self.habilitado, modelo_disponivel=self.habilitado)

    def perguntar(self, pergunta):
        self.recebidas.append(pergunta)
        if self.erro:
            raise self.erro
        return ConsultaOut.model_validate(self.resposta or RESPOSTA)


def usar(falso):
    app.dependency_overrides[get_genai] = lambda: falso
    return falso


def test_desligado_por_padrao(client):
    assert client.get("/publicacoes/saude").json() == {"habilitado": False, "servico_online": False,
                                                      "modelo_disponivel": False}
    r = client.post("/publicacoes/perguntar", json=PERGUNTA)
    assert r.status_code == 503 and r.json()["detail"]["codigo"] == "genai_desligado"


def test_consulta_devolve_resposta_com_fontes(client):
    usar(GenAIFalso())
    r = client.post("/publicacoes/perguntar", json=PERGUNTA)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "respondida" and corpo["fontes"][0]["edicao"] == 5
    assert corpo["fontes"][0]["trechos"]


def test_dados_pessoais_nao_saem_do_zelo(client):
    falso = usar(GenAIFalso())
    client.post("/publicacoes/perguntar", json={"pergunta": "Meu telefone é (11) 98765-4321, qual contrato de alimentação?"})
    assert "98765" not in falso.recebidas[0]


@pytest.mark.parametrize("erro,status,codigo", [
    (GenAITimeout("x"), 504, "genai_timeout"),
    (GenAIErro("x"), 503, "genai_indisponivel"),
    (GenAIRespostaInvalida("x"), 502, "genai_resposta_invalida"),
])
def test_falhas_viram_mensagem_clara(client, erro, status, codigo):
    usar(GenAIFalso(erro=erro))
    r = client.post("/publicacoes/perguntar", json=PERGUNTA)
    assert r.status_code == status and r.json()["detail"]["codigo"] == codigo
    assert "Traceback" not in r.text


def test_pergunta_curta_e_rejeitada(client):
    usar(GenAIFalso())
    r = client.post("/publicacoes/perguntar", json={"pergunta": "oi"})
    assert r.status_code == 422 and any("Pergunta" in c for c in r.json()["detail"]["campos"])


def test_contrato_rejeita_status_e_versao_desconhecidos():
    with pytest.raises(ValueError):
        ConsultaOut.model_validate({**RESPOSTA, "status": "inventado"})
    with pytest.raises(ValueError):
        ConsultaOut.model_validate({**RESPOSTA, "versao_contrato": "2.0"})


def test_cliente_http_trata_queda_e_contrato(monkeypatch):
    c = GenAIClient("http://localhost:8100")

    def post_caiu(*a, **k):
        raise httpx.ConnectError("recusado")
    monkeypatch.setattr(httpx, "post", post_caiu)
    with pytest.raises(GenAIErro):
        c.perguntar("pergunta de teste longa")

    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(200, json={"status": "respondida"}))
    with pytest.raises(GenAIRespostaInvalida):
        c.perguntar("pergunta de teste longa")

    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("x")))
    assert c.saude().servico_online is False
