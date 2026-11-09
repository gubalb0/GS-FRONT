import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.validacao import validar_relato  # noqa: E402


def test_relato_valido():
    assert validar_relato("Buraco grande na frente do mercado da esquina", "Centro", "06010-000", True) == []


def test_relato_curto_bairro_vazio_cep_errado_sem_consentimento():
    erros = validar_relato("buraco", "", "123", False)
    assert len(erros) == 4
