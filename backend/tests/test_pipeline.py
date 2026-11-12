import json

import pytest

from app.pipelines.privacy import mask_pii
from app.pipelines.triage import run_triage
from app.providers.llm import LLMInvalidResponse, MockLLM
from app.schemas.report import ReportInput
from tests.conftest import FakeLLM, FakeOpenData

VALIDO = {
    "categoria": "buraco_via", "urgencia": "media", "orgao_responsavel": "Subprefeitura",
    "resumo": "Buraco grande na rua principal.", "orientacoes": ["Sinalize o local."],
    "sinais_de_risco": [], "confianca": 0.9, "justificativa": "Relato descreve buraco na via.",
}


def entrada(texto, **kw):
    return ReportInput(descricao=texto, bairro="Centro", **kw)


def test_mascara_dados_pessoais():
    texto, removeu = mask_pii("Me liga no (11) 98765-4321 ou joao@email.com, CPF 123.456.789-09")
    assert removeu
    assert "98765" not in texto and "joao@" not in texto and "123.456" not in texto


def test_nao_mascara_cep_nem_numero_da_rua():
    texto, removeu = mask_pii("Rua das Flores, 25, CEP 06010-000")
    assert not removeu and "06010-000" in texto


def test_dados_pessoais_nao_chegam_ao_llm():
    llm = FakeLLM([json.dumps(VALIDO)])
    r = run_triage(entrada("Buraco enorme na rua, falar com joao@email.com urgente"), llm, FakeOpenData())
    assert r.dados_pessoais_removidos
    assert "joao@email.com" not in json.dumps(llm.chamadas[0], ensure_ascii=False)


def test_mock_classifica_alagamento():
    r = run_triage(entrada("A rua está toda alagada depois da chuva, carros parados"), MockLLM(), FakeOpenData())
    assert r.analise.categoria.value == "alagamento"
    assert r.modo == "demonstracao"


def test_chuva_forte_eleva_urgencia_de_alagamento():
    sem = run_triage(entrada("Rua alaga sempre que chove na esquina da padaria"), MockLLM(), FakeOpenData(chuva=2))
    com = run_triage(entrada("Rua alaga sempre que chove na esquina da padaria"), MockLLM(), FakeOpenData(chuva=45))
    assert sem.analise.urgencia.value == "media"
    assert com.analise.urgencia.value == "alta"
    assert com.contexto.alerta_chuva


def test_urgencia_critica_sempre_traz_numero_de_emergencia():
    critico = dict(VALIDO, urgencia="critica", orientacoes=["Afaste-se do local."])
    r = run_triage(entrada("Tem um fio caído soltando faísca na calçada"), FakeLLM([json.dumps(critico)]), FakeOpenData())
    assert any("199" in o or "193" in o for o in r.analise.orientacoes)
    assert r.precisa_revisao


def test_saida_invalida_e_corrigida_na_segunda_tentativa():
    llm = FakeLLM(["isso não é json", "```json\n" + json.dumps(VALIDO) + "\n```"])
    r = run_triage(entrada("Buraco enorme na avenida perto da escola"), llm, FakeOpenData())
    assert r.analise.categoria.value == "buraco_via"
    assert len(llm.chamadas) == 2


def test_saida_sempre_invalida_gera_erro_controlado():
    llm = FakeLLM([json.dumps({"categoria": "inventada"})] * 2)
    with pytest.raises(LLMInvalidResponse):
        run_triage(entrada("Buraco enorme na avenida perto da escola"), llm, FakeOpenData())


def test_confianca_baixa_pede_revisao():
    incerto = dict(VALIDO, confianca=0.3)
    r = run_triage(entrada("Tem uma coisa estranha na rua de casa"), FakeLLM([json.dumps(incerto)]), FakeOpenData())
    assert r.precisa_revisao


# ---------- Ajustes da validação com usuários ----------
from app.pipelines.triage import remover_telefones_inventados  # noqa: E402
from app.providers.canais import canal_para  # noqa: E402


def test_remove_telefone_inventado_pela_ia():
    # Texto real devolvido pelo LLM durante o teste com a pessoa 1
    texto = "Registre a ocorrência no aplicativo da prefeitura ou ligue para a Secretaria de Obras (0800-xxxx)."
    limpo = remover_telefones_inventados(texto)
    assert "0800" not in limpo and "xxxx" not in limpo and "()" not in limpo
    assert limpo.endswith("Secretaria de Obras.")


def test_mantem_numeros_de_emergencia_e_156():
    texto = "Ligue 199 (Defesa Civil), 193 ou 156; não ligue (11) 98888-7777."
    limpo = remover_telefones_inventados(texto)
    assert "199" in limpo and "193" in limpo and "156" in limpo and "98888" not in limpo


def test_canal_oficial_por_cidade():
    assert "SP156" in canal_para("são paulo").nome
    assert "Osasco" in canal_para(" OSASCO ").nome
    assert canal_para("Cidade Inexistente").cidade is None
    assert canal_para(None).cidade is None


def test_telefone_inventado_some_da_analise():
    inventado = dict(VALIDO, orientacoes=["Sinalize o local.", "Ligue para a Secretaria de Obras (0800-123-4567)."],
                     orgao_responsavel="Secretaria de Obras (11) 3333-4444")
    r = run_triage(entrada("Buraco enorme na avenida perto da escola"), FakeLLM([json.dumps(inventado)]), FakeOpenData())
    texto = " ".join(r.analise.orientacoes) + r.analise.orgao_responsavel
    assert "0800" not in texto and "3333" not in texto


def test_cidade_do_cep_define_o_canal():
    dados = FakeOpenData(endereco={"logradouro": "Rua X", "bairro": "Centro", "localidade": "Osasco", "uf": "SP"})
    r = run_triage(entrada("Buraco enorme na avenida perto da escola", cep="06010-000"), MockLLM(), dados)
    assert r.canal_oficial.cidade == "Osasco"


def test_sem_cidade_usa_canal_generico():
    r = run_triage(entrada("Buraco enorme na avenida perto da escola"), MockLLM(), FakeOpenData())
    assert r.canal_oficial.cidade is None and "156" in r.canal_oficial.como_registrar[0]
