"""Tela 3 — painel público e anônimo da cidade."""
import streamlit as st

from features.dados import para_dataframe
from providers import api_client as api
from providers.api_client import ApiError
from ui.charts import grafico_categorias, grafico_linha_do_tempo, grafico_urgencia
from ui.components import caixa_erro, estado_vazio
from ui.filters import filtros


def indicadores(df) -> None:
    """Linha de métricas (reaproveitada pelo painel do gestor)."""
    total = len(df)
    resolvidos = int((df["status"] == "resolvido").sum())
    graves_abertos = int((df["aberto"] & df["urgencia"].isin(["alta", "critica"])).sum())
    aceitos = 100 * (1 - df["corrigido_pelo_cidadao"].mean()) if total else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📨 Relatos", total)
    c2.metric("✅ Resolvidos", f"{resolvidos} ({resolvidos / total:.0%})" if total else "0")
    c3.metric("🟠🔴 Graves em aberto", graves_abertos)
    c4.metric("🤖 IA aceita sem correção", f"{aceitos:.0f}%")


def render() -> None:
    st.markdown("### 📊 Painel da cidade")
    st.caption("Dados anônimos de todos os relatos: sem textos, nomes ou endereços.")
    try:
        dados = api.relatos_publicos()
    except ApiError as erro:
        caixa_erro(erro)
        return
    df = para_dataframe(dados)
    if df.empty:
        estado_vazio("🏙️", "Ainda não há relatos", "Seja a primeira pessoa a relatar um problema na sua rua!")
        return
    if df["demo"].fillna(False).any():
        st.info("Este painel inclui relatos **fictícios** de demonstração, criados para ilustrar o funcionamento.",
                icon="ℹ️")

    filtrado = filtros(df, "cidade", mostrar_status=True, mostrar_bairro=True)
    if filtrado.empty:
        estado_vazio("🔍", "Nada encontrado", "Nenhum relato com esses filtros. Tente ampliar o período ou remover filtros.")
        return

    indicadores(filtrado)
    hc = st.session_state.alto_contraste
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(grafico_categorias(filtrado, hc), width="stretch")
    c2.plotly_chart(grafico_urgencia(filtrado, hc), width="stretch")
    st.plotly_chart(grafico_linha_do_tempo(filtrado, hc), width="stretch")
