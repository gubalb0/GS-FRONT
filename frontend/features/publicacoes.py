"""Aba "Publicações oficiais": consulta ao Diário Oficial do DF (saúde) pelo assistente de Generative AI do grupo.

Integração isolada: o Zelo chama o serviço `integracao_citizentech` (pasta 05_Generative_AI / 01_RPA do repositório
GS-CitizenTech), que roda junto do LM Studio no computador da demonstração. No Render o recurso fica desligado.
"""
import html

import streamlit as st

from providers import api_client as api
from providers.api_client import ApiError
from ui.components import caixa_erro, estado_vazio, seguro

EXEMPLOS = [  # perguntas reais do conjunto de validação usado pelo módulo de Gen AI (dodf-saude-qa)
    "Qual é o serviço de alimentação hospitalar contratado para as unidades de saúde em Ceilândia?",
    "Qual instituição de saúde em Ceilândia teve seu crédito orçamentário descentralizado para pagamento de despesas de exercícios anteriores?",
    "Qual é o valor autorizado para pagamento ao Hospital das Clínicas e Pronto Socorro de Fraturas?",
    "Qual é a capital da França?",
]
ESTILO = {  # cor + ícone + texto (nunca só cor)
    "respondida": ("✅", "#14532D", "#DCFCE7"),
    "parcial": ("🟡", "#713F12", "#FEF9C3"),
    "ambigua": ("🔀", "#1E3A8A", "#DBEAFE"),
    "insuficiente": ("⚪", "#334155", "#E2E8F0"),
    "fora_do_escopo": ("🚫", "#7C2D12", "#FFEDD5"),
    "indisponivel": ("🔌", "#7F1D1D", "#FEE2E2"),
}


def render() -> None:
    st.markdown("### Publicações oficiais")
    st.caption("Pergunte sobre contratos, compras e atos de saúde publicados no **Diário Oficial do Distrito Federal**. "
               "O assistente responde só com o que está nas publicações, mostra de onde tirou a informação e "
               "prefere não responder quando não tem certeza.")
    with st.expander("Sobre este recurso"):
        st.markdown(
            "- É o módulo de **Generative AI** do grupo: busca BM25 em 1.381 publicações de saúde do DODF + modelo "
            "local Qwen3-8B + verificação das citações no código.\n"
            "- É um **protótipo acadêmico não validado**: na avaliação com 150 perguntas, ele se absteve em cerca de "
            "70% e algumas respostas citaram a publicação errada. Confira sempre a fonte.\n"
            "- Não trata de zeladoria nem de Osasco/São Paulo: o conjunto de dados público disponível é do DF.\n"
            "- Cada resposta leva de 15 a 30 segundos, porque o modelo roda no computador da demonstração.")

    try:
        saude = api.publicacoes_saude()
    except ApiError as erro:
        caixa_erro(erro)
        return
    if not saude["habilitado"]:
        estado_vazio("🖥️", "Disponível só na demonstração local",
                     "Este recurso precisa de um modelo de linguagem rodando no computador (LM Studio), por isso não "
                     "funciona na versão publicada. O passo a passo está em docs/INTEGRACAO_GENAI.md no repositório.")
        return
    if not saude["servico_online"]:
        st.error("O serviço do assistente não está respondendo. Inicie-o com "
                 "`uvicorn integracao_citizentech.api:app --port 8100` na pasta do módulo.", icon="🔌")
        return
    if not saude["modelo_disponivel"]:
        st.warning("O serviço está ligado, mas o modelo não está carregado no LM Studio. Abra o LM Studio e "
                   "carregue o modelo com o identificador `qwen3-8b`.", icon="⚠️")

    st.markdown("**Exemplos** (perguntas do conjunto de avaliação do módulo):")
    colunas = st.columns(2)
    for i, exemplo in enumerate(EXEMPLOS):
        if colunas[i % 2].button(exemplo, key=f"pub_ex_{i}", width="stretch"):
            st.session_state.pub_pergunta = exemplo

    with st.form("form_publicacoes"):
        pergunta = st.text_area("Sua pergunta *", key="pub_pergunta", max_chars=500, height=90,
                                placeholder="Ex.: Qual empresa foi contratada para a manutenção da autoclave da policlínica?")
        enviar = st.form_submit_button("Consultar publicações", type="primary", width="stretch")
    if not enviar:
        return
    if len((pergunta or "").strip()) < 10:
        st.warning("Escreva a pergunta com pelo menos 10 letras.", icon="✍️")
        return
    with st.status("Consultando o Diário Oficial…", expanded=True) as status:
        st.write("Buscando as publicações mais parecidas com a pergunta…")
        st.write("O modelo está lendo os trechos (leva de 15 a 30 s)…")
        try:
            r = api.perguntar_publicacoes(pergunta.strip())
        except ApiError as erro:
            status.update(label="Não foi possível consultar agora", state="error", expanded=False)
            caixa_erro(erro)
            return
        status.update(label="Consulta concluída", state="complete", expanded=False)
    _resultado(r)


def _resultado(r: dict) -> None:
    icone, fg, bg = ESTILO.get(r["status"], ESTILO["insuficiente"])
    st.markdown(f'<span class="zelo-badge" style="color:{fg};background:{bg}"><span aria-hidden="true">{icone}</span> '
                f'{html.escape(r["rotulo_status"])}</span>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(seguro(r["resposta"]))
        if r.get("aviso"):
            st.caption(r["aviso"])
    if r["fontes"]:
        st.markdown(f"**{'Publicação citada' if len(r['fontes']) == 1 else 'Publicações citadas'}**")
        for f in r["fontes"]:
            titulo = " – ".join(str(x) for x in (f.get("tipo_documento"), f.get("numero_documento")) if x) or "Publicação"
            with st.container(border=True):
                st.markdown(f"**{seguro(titulo)}**")
                st.caption(f"DODF edição {seguro(str(f.get('edicao') or '?'))} · {seguro(f.get('data_edicao') or '?')} · "
                           f"{seguro(f.get('secao') or '')}")
                for t in f.get("trechos") or []:
                    st.markdown(f"> “{seguro(t)}”")
    detalhes = [f"política {r['versao_politica']}"]
    if r.get("latencia_s") is not None:
        detalhes.append(f"{r['latencia_s']} s")
    st.caption("Gerado por IA a partir das publicações acima · " + " · ".join(detalhes))
