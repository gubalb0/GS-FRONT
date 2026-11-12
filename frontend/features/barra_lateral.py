import streamlit as st

from providers import api_client as api
from providers.api_client import ApiError
from ui.components import botoes_emergencia


def render() -> None:
    with st.sidebar:
        st.markdown("## Zelo")
        st.caption("Viu um problema na rua? Conte para nós: o sistema organiza o pedido, você confere "
                   "e mostramos onde registrar na prefeitura.")

        st.radio("Você é:", ["Cidadão", "Gestor"], key="perfil", horizontal=True,
                 help="Gestores tratam os relatos e precisam de senha.")

        st.markdown("#### ♿ Acessibilidade")
        st.toggle("Alto contraste", key="alto_contraste")
        st.toggle("Letras maiores", key="fonte_grande")
        st.caption("Dica: use **Tab** para navegar e **Enter** para acionar botões.")

        st.markdown("#### Situação do serviço")
        try:
            saude = api.saude()
            modo = "classificação automática ativa" if saude.get("modo") == "ia" else "modo demonstração"
            st.success(f"Online · {modo}", icon="🟢")
        except ApiError:
            st.error("Serviço fora do ar no momento. Tente mais tarde.", icon="🔴")

        st.markdown("#### Emergência")
        st.markdown(f'<div class="zelo-tels">{botoes_emergencia()}</div>', unsafe_allow_html=True)
        st.caption("No celular, toque no número para ligar. Para pedidos que não são emergência, use o 156.")
        st.caption("🔒 Não informe CPF, telefone ou e-mail. Se informar, eles são apagados antes da análise.")
