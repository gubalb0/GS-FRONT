"""Bloco de filtros reutilizável (usado em 'Meus relatos', 'Painel da cidade' e na fila do gestor)."""
from datetime import date

import pandas as pd
import streamlit as st

from ui.rotulos import ORDEM_URGENCIA, STATUS, rotulo_categoria, rotulo_status, rotulo_urgencia


def filtros(df: pd.DataFrame, chave: str, *, mostrar_status: bool = True, mostrar_bairro: bool = False,
            mostrar_periodo: bool = True) -> pd.DataFrame:
    """Desenha os controles e devolve o DataFrame filtrado. `chave` evita colisão de widgets entre telas."""
    if df.empty:
        return df
    with st.container(border=True):
        st.markdown("**🔎 Filtrar**")
        colunas = st.columns(2 + mostrar_status + mostrar_bairro + mostrar_periodo)
        i = 0
        cats = colunas[i].multiselect("Tipo de problema", sorted(df["categoria"].unique()),
                                      format_func=rotulo_categoria, key=f"{chave}_cat", placeholder="Todos")
        i += 1
        urgs = colunas[i].multiselect("Urgência", [u for u in ORDEM_URGENCIA if u in set(df["urgencia"])],
                                      format_func=rotulo_urgencia, key=f"{chave}_urg", placeholder="Todas")
        i += 1
        stats: list[str] = []
        if mostrar_status:
            stats = colunas[i].multiselect("Situação", [s for s in STATUS if s in set(df["status"])],
                                           format_func=rotulo_status, key=f"{chave}_st", placeholder="Todas")
            i += 1
        bairros: list[str] = []
        if mostrar_bairro:
            bairros = colunas[i].multiselect("Bairro", sorted(df["bairro"].unique()), key=f"{chave}_bairro",
                                             placeholder="Todos")
            i += 1
        periodo = None
        if mostrar_periodo:
            inicio, fim = df["data"].min(), df["data"].max()
            periodo = colunas[i].date_input("Período", value=(inicio, fim), min_value=inicio, max_value=fim,
                                            format="DD/MM/YYYY", key=f"{chave}_periodo")

    filtro = pd.Series(True, index=df.index)
    if cats:
        filtro &= df["categoria"].isin(cats)
    if urgs:
        filtro &= df["urgencia"].isin(urgs)
    if stats:
        filtro &= df["status"].isin(stats)
    if bairros:
        filtro &= df["bairro"].isin(bairros)
    if isinstance(periodo, (tuple, list)) and len(periodo) == 2 and all(isinstance(d, date) for d in periodo):
        filtro &= (df["data"] >= periodo[0]) & (df["data"] <= periodo[1])
    resultado = df[filtro]
    st.caption(f"Mostrando **{len(resultado)}** de {len(df)} relato(s).")
    return resultado
