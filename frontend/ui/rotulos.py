"""Textos, ícones e cores semânticas. Cor NUNCA aparece sozinha: sempre com ícone e texto."""

CATEGORIAS = {
    "buraco_via": ("🕳️", "Buraco ou asfalto danificado"),
    "iluminacao_publica": ("💡", "Iluminação pública"),
    "lixo_entulho": ("🗑️", "Lixo ou entulho"),
    "alagamento": ("🌊", "Alagamento ou enchente"),
    "arvore_risco": ("🌳", "Árvore com risco de queda"),
    "calcada_acessibilidade": ("♿", "Calçada e acessibilidade"),
    "sinalizacao_transito": ("🚦", "Sinalização e semáforo"),
    "agua_esgoto": ("🚰", "Água e esgoto"),
    "outro": ("📌", "Outro problema"),
}

# fg/bg com contraste AA (≥ 4.5:1); "cor" é usada nos gráficos.
URGENCIAS = {
    "baixa": {"icone": "🟢", "rotulo": "Baixa", "fg": "#14532D", "bg": "#DCFCE7", "cor": "#16A34A",
              "dica": "Pode aguardar o atendimento de rotina."},
    "media": {"icone": "🟡", "rotulo": "Média", "fg": "#713F12", "bg": "#FEF9C3", "cor": "#CA8A04",
              "dica": "Deve ser resolvido nos próximos dias."},
    "alta": {"icone": "🟠", "rotulo": "Alta", "fg": "#7C2D12", "bg": "#FFEDD5", "cor": "#EA580C",
             "dica": "Precisa de atenção rápida."},
    "critica": {"icone": "🔴", "rotulo": "Crítica", "fg": "#7F1D1D", "bg": "#FEE2E2", "cor": "#DC2626",
                "dica": "Risco imediato. Se houver perigo, ligue 199 ou 193."},
}
ORDEM_URGENCIA = ["baixa", "media", "alta", "critica"]

STATUS = {
    "recebido": ("📥", "Recebido"),
    "em_analise": ("🔎", "Em análise"),
    "encaminhado": ("📤", "Encaminhado ao órgão"),
    "resolvido": ("✅", "Resolvido"),
    "recusado": ("⛔", "Não procede"),
}
STATUS_ABERTOS = {"recebido", "em_analise", "encaminhado"}


def rotulo_categoria(cat: str) -> str:
    icone, texto = CATEGORIAS.get(cat, ("📌", cat))
    return f"{icone} {texto}"


def rotulo_urgencia(urg: str) -> str:
    u = URGENCIAS.get(urg)
    return f"{u['icone']} {u['rotulo']}" if u else urg


def rotulo_status(st_: str) -> str:
    icone, texto = STATUS.get(st_, ("•", st_))
    return f"{icone} {texto}"
