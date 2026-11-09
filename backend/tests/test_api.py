from app.dependencies import get_llm, get_open_data
from app.main import app
from app.providers.llm import LLMError, LLMRateLimit, LLMTimeout
from tests.conftest import FakeLLM, FakeOpenData

RELATO = {"descricao": "Poste apagado há uma semana na rua da escola, fica tudo escuro", "bairro": "Centro"}


def _sem_rede():
    app.dependency_overrides[get_open_data] = lambda: FakeOpenData()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["modo"] == "demonstracao"


def test_validacao_amigavel(client):
    r = client.post("/reports/analyze", json={"descricao": "curto", "bairro": "", "cep": "123"})
    assert r.status_code == 422
    detalhe = r.json()["detail"]
    assert detalhe["codigo"] == "entrada_invalida"
    assert any("Descrição" in c for c in detalhe["campos"])
    assert any("CEP" in c for c in detalhe["campos"])


def test_fluxo_completo_com_correcao_do_cidadao(client):
    _sem_rede()
    analise = client.post("/reports/analyze", json=RELATO).json()
    assert analise["analise"]["categoria"] == "iluminacao_publica"

    r = client.post("/reports", json={"analise_id": analise["analise_id"],
                                      "categoria_final": "iluminacao_publica", "urgencia_final": "critica"})
    assert r.status_code == 201
    relato = r.json()
    assert relato["protocolo"].startswith("ZL-")
    assert relato["urgencia_ia"] == analise["analise"]["urgencia"]  # guarda o que a IA disse
    assert relato["corrigido_pelo_cidadao"] is True  # cidadão alterou a urgência
    # mesma análise não pode ser enviada duas vezes
    again = client.post("/reports", json={"analise_id": analise["analise_id"],
                                          "categoria_final": "outro", "urgencia_final": "baixa"})
    assert again.status_code == 404

    meus = client.get("/reports/mine", params={"protocolos": relato["protocolo"]}).json()
    assert meus[0]["protocolo"] == relato["protocolo"]

    fb = client.patch(f"/reports/{relato['protocolo']}/feedback", json={"util": True})
    assert fb.json()["feedback_util"] is True


def test_painel_publico_nao_expoe_descricao(client):
    _sem_rede()
    a = client.post("/reports/analyze", json=RELATO).json()
    client.post("/reports", json={"analise_id": a["analise_id"], "categoria_final": "iluminacao_publica",
                                  "urgencia_final": "media"})
    publico = client.get("/reports/public").json()
    assert publico and "descricao" not in publico[0] and "protocolo" not in publico[0]


def test_timeout_da_ia_vira_mensagem_clara(client):
    _sem_rede()
    app.dependency_overrides[get_llm] = lambda: FakeLLM(erro=LLMTimeout("x"))
    r = client.post("/reports/analyze", json=RELATO)
    assert r.status_code == 504
    assert r.json()["detail"]["codigo"] == "ia_timeout"
    assert "Traceback" not in r.text


def test_ia_fora_do_ar(client):
    _sem_rede()
    app.dependency_overrides[get_llm] = lambda: FakeLLM(erro=LLMError("x"))
    r = client.post("/reports/analyze", json=RELATO)
    assert r.status_code == 503 and r.json()["detail"]["codigo"] == "ia_indisponivel"


def test_gestor_exige_login(client):
    assert client.get("/manager/reports").status_code == 401
    assert client.post("/auth/login", json={"senha": "errada"}).status_code == 401


def test_gestor_atualiza_status(client):
    _sem_rede()
    a = client.post("/reports/analyze", json=RELATO).json()
    relato = client.post("/reports", json={"analise_id": a["analise_id"], "categoria_final": "iluminacao_publica",
                                           "urgencia_final": "media"}).json()
    token = client.post("/auth/login", json={"senha": "senha-teste"}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/manager/reports", headers=h).status_code == 200
    r = client.patch(f"/manager/reports/{relato['id']}/status", headers=h,
                     json={"status": "encaminhado", "nota": "Enviado à equipe de iluminação"})
    assert r.json()["status"] == "encaminhado"


def test_cors_restritivo(client):
    ok = client.options("/health", headers={"Origin": "http://localhost:8501", "Access-Control-Request-Method": "GET"})
    bloqueado = client.options("/health", headers={"Origin": "https://site-malicioso.com", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8501"
    assert "access-control-allow-origin" not in bloqueado.headers


def test_limite_de_requisicoes(client):
    _sem_rede()
    app.dependency_overrides[get_llm] = lambda: FakeLLM(erro=LLMRateLimit("x"))
    r = client.post("/reports/analyze", json=RELATO)
    assert r.status_code == 429 and r.json()["detail"]["codigo"] == "ia_ocupada"
