"""Gráficos Plotly (interativos: hover, zoom, legenda clicável). Urgência usa cor + padrão de textura + texto."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.rotulos import ORDEM_URGENCIA, URGENCIAS, rotulo_urgencia

ROTULOS_URG = [rotulo_urgencia(u) for u in ORDEM_URGENCIA]
CORES_URG = {rotulo_urgencia(u): URGENCIAS[u]["cor"] for u in ORDEM_URGENCIA}
PADROES_URG = {rotulo_urgencia(u): p for u, p in zip(ORDEM_URGENCIA, ["", "/", "x", "."])}


def _estilo(fig: go.Figure, titulo: str, alto_contraste: bool) -> go.Figure:
    fig.update_layout(
        template="plotly_dark" if alto_contraste else "plotly_white",
        title={"text": titulo, "font": {"size": 17}},
        font={"size": 14},
        hoverlabel={"font_size": 14},
        legend_title_text="",
        margin={"l": 10, "r": 10, "t": 56, "b": 10},
    )
    return fig


def grafico_categorias(df: pd.DataFrame, alto_contraste: bool = False) -> go.Figure:
    dados = df.groupby(["categoria_rotulo", "urgencia_rotulo"]).size().reset_index(name="relatos")
    ordem = dados.groupby("categoria_rotulo")["relatos"].sum().sort_values().index.tolist()
    fig = px.bar(
        dados, x="relatos", y="categoria_rotulo", color="urgencia_rotulo", orientation="h",
        pattern_shape="urgencia_rotulo", pattern_shape_map=PADROES_URG,
        color_discrete_map=CORES_URG,
        category_orders={"urgencia_rotulo": ROTULOS_URG, "categoria_rotulo": ordem},
        labels={"relatos": "Relatos", "categoria_rotulo": "", "urgencia_rotulo": "Urgência"},
    )
    fig.update_traces(hovertemplate="%{y}<br>%{fullData.name}: <b>%{x}</b> relato(s)<extra></extra>")
    return _estilo(fig, "Problemas por tipo e urgência", alto_contraste)


def grafico_linha_do_tempo(df: pd.DataFrame, alto_contraste: bool = False) -> go.Figure:
    dados = (df.assign(situacao=df["aberto"].map({True: "Em aberto", False: "Finalizados"}))
             .groupby(["data", "situacao"]).size().reset_index(name="relatos"))
    fig = px.line(dados, x="data", y="relatos", color="situacao", markers=True, symbol="situacao",
                  color_discrete_map={"Em aberto": "#EA580C", "Finalizados": "#0B6E4F"},
                  labels={"data": "Dia", "relatos": "Relatos", "situacao": ""})
    fig.update_xaxes(rangeslider_visible=True, tickformat="%d/%m")
    fig.update_traces(hovertemplate="%{x|%d/%m/%Y}: <b>%{y}</b> relato(s)<extra>%{fullData.name}</extra>")
    return _estilo(fig, "Linha do tempo dos relatos", alto_contraste)


def grafico_urgencia(df: pd.DataFrame, alto_contraste: bool = False) -> go.Figure:
    dados = df["urgencia_rotulo"].value_counts().reindex(ROTULOS_URG).dropna().reset_index()
    dados.columns = ["urgencia", "relatos"]
    fig = px.pie(dados, names="urgencia", values="relatos", hole=0.55, color="urgencia",
                 color_discrete_map=CORES_URG, category_orders={"urgencia": ROTULOS_URG})
    fig.update_traces(textinfo="label+percent", sort=False,
                      hovertemplate="%{label}: <b>%{value}</b> relato(s)<extra></extra>")
    return _estilo(fig, "Distribuição por urgência", alto_contraste)


def grafico_qualidade_ia(df: pd.DataFrame, alto_contraste: bool = False) -> go.Figure:
    dados = (df.groupby("categoria_rotulo")
             .agg(total=("protocolo_ou_idx", "size"), corrigidos=("corrigido_pelo_cidadao", "sum"))
             .reset_index())
    dados["acerto"] = (1 - dados["corrigidos"] / dados["total"]) * 100
    dados = dados.sort_values("acerto")
    fig = px.bar(dados, x="acerto", y="categoria_rotulo", orientation="h", text=dados["acerto"].map("{:.0f}%".format),
                 labels={"acerto": "% aceito sem correção", "categoria_rotulo": ""},
                 color_discrete_sequence=["#0B6E4F"], hover_data={"total": True, "corrigidos": True})
    fig.update_xaxes(range=[0, 105])
    return _estilo(fig, "Acerto da IA por tipo (segundo o cidadão)", alto_contraste)
