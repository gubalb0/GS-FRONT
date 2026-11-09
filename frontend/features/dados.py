"""Transforma relatos (lista de dicts) em DataFrame pronto para filtros e gráficos."""
import pandas as pd

from ui.rotulos import STATUS_ABERTOS, rotulo_categoria, rotulo_status, rotulo_urgencia

COLUNAS = ["categoria", "urgencia", "status", "bairro", "criado_em", "corrigido_pelo_cidadao", "feedback_util"]


def para_dataframe(relatos: list[dict]) -> pd.DataFrame:
    if not relatos:
        return pd.DataFrame(columns=COLUNAS + ["data", "aberto"])
    df = pd.DataFrame(relatos)
    for col in COLUNAS:
        if col not in df:
            df[col] = None
    df["criado_em"] = pd.to_datetime(df["criado_em"], utc=True, format="ISO8601").dt.tz_convert("America/Sao_Paulo")
    df["data"] = df["criado_em"].dt.date
    df["aberto"] = df["status"].isin(STATUS_ABERTOS)
    df["categoria_rotulo"] = df["categoria"].map(rotulo_categoria)
    df["urgencia_rotulo"] = df["urgencia"].map(rotulo_urgencia)
    df["status_rotulo"] = df["status"].map(rotulo_status)
    df["corrigido_pelo_cidadao"] = df["corrigido_pelo_cidadao"].fillna(False).astype(bool)
    df["protocolo_ou_idx"] = df["protocolo"] if "protocolo" in df else df.index
    return df
