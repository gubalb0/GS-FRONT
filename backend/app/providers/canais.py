"""Canais OFICIAIS de atendimento por cidade.

Vêm de fontes públicas verificadas (links em `fonte`), nunca da IA — o LLM chegou a inventar
"Secretaria de Obras (0800-xxxx)" durante a validação com usuários, então o canal passou a ser
determinístico. Para incluir uma cidade, adicione uma entrada com fonte oficial.
"""
import unicodedata

from app.schemas.report import CanalOficial

CANAIS: dict[str, CanalOficial] = {
    "sao paulo": CanalOficial(
        cidade="São Paulo",
        nome="SP156 – Central de atendimento da Prefeitura de São Paulo",
        como_registrar=[
            "Aplicativo SP156 (Android e iOS)",
            "Portal: sp156.prefeitura.sp.gov.br",
            "WhatsApp: (11) 3230-5156",
            "Telefone: 156",
        ],
        fonte="https://prefeitura.sp.gov.br/web/ipiranga/w/opera%C3%A7%C3%A3o-tapa-buraco-no-ipiranga-saiba-como-solicitar-o-servi%C3%A7o",
    ),
    "osasco": CanalOficial(
        cidade="Osasco",
        nome="Central 156 – Prefeitura de Osasco (24 horas)",
        como_registrar=[
            "Aplicativo 156 Osasco (Android e iOS)",
            "Portal: central156.osasco.sp.gov.br",
            "Telefone: 156 ou (11) 3651-7080",
        ],
        fonte="https://osasco.sp.gov.br/faq-3/",
    ),
}

CANAL_GENERICO = CanalOficial(
    cidade=None,
    nome="Central de atendimento da sua prefeitura",
    como_registrar=[
        "Ligue 156 (número usado pela maioria das prefeituras)",
        "Ou procure \"156\" ou \"Ouvidoria\" no site oficial da sua cidade",
    ],
    fonte=None,
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().replace("-", " ").split())


def canal_para(cidade: str | None) -> CanalOficial:
    if not cidade:
        return CANAL_GENERICO
    return CANAIS.get(_normalizar(cidade), CANAL_GENERICO)
