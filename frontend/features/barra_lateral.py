import streamlit as st

from providers import api_client as api
from providers.api_client import ApiError


def render() -> None:
    with st.sidebar:
        st.markdown("## 🏙️ Zelo")
        st.caption("Viu um problema na rua? Conte para nós. A IA organiza, você confere e a prefeitura age.")

        st.radio("Você é:", ["Cidadão", "Gestor"], key="perfil", horizontal=True,
                 help="Gestores tratam os relatos e precisam de senha.")

        st.markdown("#### ♿ Acessibilidade")
        st.toggle("Alto contraste", key="alto_contraste")
        st.toggle("Letras maiores", key="fonte_grande")
        st.caption("Dica: use **Tab** para navegar e **Enter** para acionar botões.")

        st.markdown("#### Situação do serviço")
        try:
            saude = api.saude()
            modo = "IA ativa" if saude.get("modo") == "ia" else "modo demonstração"
            st.success(f"Online · {modo}", icon="🟢")
        except ApiError:
            st.error("Serviço fora do ar no momento. Tente mais tarde.", icon="🔴")

        st.markdown("#### 🚨 Emergência")
        st.markdown("- **199** Defesa Civil\n- **193** Bombeiros\n- **192** SAMU\n- **156** Prefeitura")
        st.caption("🔒 Não informe CPF, telefone ou e-mail. Se informar, eles são apagados antes de chegar à IA.")
