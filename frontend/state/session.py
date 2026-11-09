"""Estado centralizado da sessão. Nenhuma outra camada escreve em st.session_state diretamente
(exceto widgets com key=, que o Streamlit sincroniza sozinho)."""
import copy

import streamlit as st

PADRAO = {
    "etapa": "formulario",      # formulario -> revisao -> concluido
    "rascunho": {},             # o que o cidadão digitou (sobrevive a reruns e ao "voltar e editar")
    "analise_atual": None,      # resposta da IA aguardando confirmação
    "ultimo_relato": None,      # relato recém-protocolado
    "historico": [],            # todos os relatos desta sessão (alimenta lista e gráficos)
    "perfil": "Cidadão",
    "token_gestor": None,
    "alto_contraste": False,
    "fonte_grande": False,
}


def iniciar_estado() -> None:
    for chave, valor in PADRAO.items():
        if chave not in st.session_state:
            st.session_state[chave] = copy.deepcopy(valor)


def ir_para(etapa: str) -> None:
    st.session_state.etapa = etapa


def guardar_rascunho(**campos) -> None:
    st.session_state.rascunho = campos


def guardar_analise(analise: dict) -> None:
    st.session_state.analise_atual = analise
    for chave in ("hitl_categoria", "hitl_urgencia"):  # a nova análise define os valores iniciais
        st.session_state.pop(chave, None)
    ir_para("revisao")


def registrar_relato(relato: dict) -> None:
    st.session_state.ultimo_relato = relato
    st.session_state.historico.insert(0, relato)
    st.session_state.analise_atual = None
    st.session_state.rascunho = {}
    _limpar_formulario()
    ir_para("concluido")


def _limpar_formulario() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("f_")]:
        del st.session_state[chave]


def novo_relato() -> None:
    _limpar_formulario()
    st.session_state.analise_atual = None
    st.session_state.ultimo_relato = None
    st.session_state.rascunho = {}
    ir_para("formulario")


def atualizar_historico(relatos: list[dict]) -> None:
    """Substitui itens do histórico pelas versões mais recentes vindas da API."""
    novos = {r["protocolo"]: r for r in relatos}
    st.session_state.historico = [novos.get(r["protocolo"], r) for r in st.session_state.historico]


def protocolos() -> tuple[str, ...]:
    return tuple(r["protocolo"] for r in st.session_state.historico)


def entrar_como_gestor(token: str) -> None:
    st.session_state.token_gestor = token


def sair_do_gestor() -> None:
    st.session_state.token_gestor = None
