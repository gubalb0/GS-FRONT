"""Zelo — front-end Streamlit. Este arquivo só monta o layout; a lógica fica em features/, ui/, state/ e providers/."""
import streamlit as st

st.set_page_config(page_title="Zelo · Zeladoria urbana com IA", page_icon="🏙️", layout="wide",
                   initial_sidebar_state="expanded")

from features import barra_lateral, gestor, meus_relatos, novo_relato, painel_cidade  # noqa: E402
from state.session import iniciar_estado  # noqa: E402
from ui.theme import aplicar_tema  # noqa: E402

iniciar_estado()
barra_lateral.render()
aplicar_tema(st.session_state.alto_contraste, st.session_state.fonte_grande)

st.markdown(
    '<header class="zelo-hero"><h1>🏙️ Zelo</h1>'
    "<p>Buraco, poste apagado, lixo, alagamento? Relate em 1 minuto. "
    "A IA entende, você confere e a prefeitura recebe tudo organizado.</p></header>",
    unsafe_allow_html=True,
)

if st.session_state.perfil == "Gestor":
    gestor.render()
else:
    aba_novo, aba_meus, aba_cidade = st.tabs(["📝 Novo relato", "📋 Meus relatos", "📊 Painel da cidade"])
    with aba_novo:
        novo_relato.render()
    with aba_meus:
        meus_relatos.render()
    with aba_cidade:
        painel_cidade.render()
