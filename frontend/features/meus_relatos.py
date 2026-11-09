"""Tela 2 — histórico do cidadão (vive no st.session_state) + avaliação da resposta da IA."""
import streamlit as st

from features.dados import para_dataframe
from providers import api_client as api
from providers.api_client import ApiError
from state import session
from ui.charts import grafico_categorias
from ui.components import caixa_erro, cartao_relato, estado_vazio
from ui.filters import filtros


def render() -> None:
    st.markdown("### 📋 Meus relatos")
    historico = st.session_state.historico
    if not historico:
        estado_vazio("📭", "Você ainda não fez nenhum relato",
                     "Quando enviar um relato na aba “Novo relato”, ele aparece aqui com o protocolo e a situação.")
        return

    topo1, topo2 = st.columns([3, 1])
    topo1.caption("Seus relatos ficam guardados enquanto esta janela estiver aberta. Anote os protocolos!")
    if topo2.button("🔄 Atualizar situação", width="stretch"):
        try:
            session.atualizar_historico(api.meus_relatos(session.protocolos()))
            st.toast("Situação atualizada.", icon="✅")
        except ApiError as erro:
            caixa_erro(erro)

    df = para_dataframe(historico)
    filtrado = filtros(df, "meus", mostrar_status=True, mostrar_periodo=False)
    if filtrado.empty:
        estado_vazio("🔍", "Nenhum relato com esses filtros", "Remova algum filtro para ver seus relatos.")
        return

    if len(filtrado) > 1:
        st.plotly_chart(grafico_categorias(filtrado, st.session_state.alto_contraste), width="stretch")

    visiveis = set(filtrado["protocolo"])
    for relato in [r for r in historico if r["protocolo"] in visiveis]:
        cartao_relato(relato, mostrar_descricao=True)
        _feedback(relato)


def _feedback(relato: dict) -> None:
    if relato.get("feedback_util") is not None:
        st.caption("Obrigado! Você avaliou esta resposta como "
                   + ("👍 útil." if relato["feedback_util"] else "👎 incorreta."))
        return
    st.markdown("**A orientação da IA foi útil?**")
    c1, c2, _ = st.columns([1, 1, 3])
    util = None
    if c1.button("👍 Sim, foi útil", key=f"fb_ok_{relato['protocolo']}"):
        util = True
    if c2.button("👎 Estava errada", key=f"fb_no_{relato['protocolo']}"):
        util = False
    if util is not None:
        try:
            session.atualizar_historico([api.enviar_feedback(relato["protocolo"], util)])
            st.rerun()
        except ApiError as erro:
            caixa_erro(erro)
