"""Primeiro contato com a API. No plano gratuito do Render a API "dorme" e leva até ~1 min para acordar;
sem aviso, isso parecia travamento (pessoa 3 da validação). Aqui o cidadão vê o que está acontecendo."""
import streamlit as st

from providers import api_client as api

ESPERA_RAPIDA_S = 3
ESPERA_ACORDAR_S = 75


def garantir_api_acordada() -> None:
    if st.session_state.get("api_acordada"):
        return
    if api.api_respondendo(ESPERA_RAPIDA_S):
        st.session_state.api_acordada = True
        return
    aviso = st.empty()
    with aviso.container():
        with st.status("Conectando ao serviço…", expanded=True) as status:
            st.write("O servidor estava em repouso para economizar energia e está ligando agora.")
            st.write("Isso acontece só no primeiro acesso e leva **até 1 minuto**. Não feche a página.")
            acordou = api.api_respondendo(ESPERA_ACORDAR_S)
            if acordou:
                status.update(label="Pronto! Serviço conectado.", state="complete", expanded=False)
    if acordou:
        st.session_state.api_acordada = True
        api.saude.clear()
        aviso.empty()
    else:
        aviso.error("Não conseguimos ligar o serviço agora. Tente recarregar a página em alguns minutos.", icon="⚠️")
