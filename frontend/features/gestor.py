"""Visão do gestor (RBAC): fila priorizada, mudança de status e qualidade da IA."""
import streamlit as st

from features.dados import para_dataframe
from features.painel_cidade import indicadores
from providers import api_client as api
from providers.api_client import ApiError
from state import session
from ui.charts import grafico_categorias, grafico_linha_do_tempo, grafico_qualidade_ia
from ui.components import caixa_erro, cartao_relato, estado_vazio
from ui.filters import filtros
from ui.rotulos import STATUS, rotulo_status

MAX_NA_FILA = 25


def render() -> None:
    token = st.session_state.token_gestor
    if not token:
        _login()
        return

    topo, sair = st.columns([4, 1])
    topo.markdown("### 🛡️ Área do gestor")
    if sair.button("Sair", width="stretch"):
        session.sair_do_gestor()
        st.rerun()

    try:
        relatos = api.relatos_gestor(token)
    except ApiError as erro:
        if erro.status == 401:
            session.sair_do_gestor()
            st.warning("Sua sessão expirou. Entre novamente.", icon="🔐")
            st.button("Entrar novamente")
        else:
            caixa_erro(erro)
        return

    df = para_dataframe(relatos)
    if df.empty:
        estado_vazio("📭", "Fila vazia", "Nenhum relato recebido até agora.")
        return

    aba_fila, aba_ind = st.tabs(["📋 Fila de atendimento", "📈 Indicadores e qualidade da IA"])
    with aba_fila:
        filtrado = filtros(df, "gestor", mostrar_status=True, mostrar_bairro=True)
        if filtrado.empty:
            estado_vazio("🔍", "Nada com esses filtros", "Ajuste os filtros para ver a fila.")
        else:
            ordem = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
            fila = filtrado.assign(_p=filtrado["urgencia"].map(ordem), _a=~filtrado["aberto"]) \
                           .sort_values(["_a", "_p", "criado_em"])
            st.caption(f"Ordenado por: em aberto primeiro → urgência → mais antigo. "
                       f"Mostrando até {MAX_NA_FILA}.")
            por_id = {r["id"]: r for r in relatos}
            for rid in fila["id"].head(MAX_NA_FILA):
                _item(por_id[rid], token)
    with aba_ind:
        indicadores(df)
        hc = st.session_state.alto_contraste
        c1, c2 = st.columns(2)
        c1.plotly_chart(grafico_categorias(df, hc), width="stretch")
        c2.plotly_chart(grafico_qualidade_ia(df, hc), width="stretch")
        st.plotly_chart(grafico_linha_do_tempo(df, hc), width="stretch")
        avaliados = df["feedback_util"].dropna()
        if len(avaliados):
            st.caption(f"👍 {avaliados.astype(bool).mean():.0%} dos cidadãos que avaliaram acharam a orientação útil "
                       f"({len(avaliados)} avaliações).")


def _item(relato: dict, token: str) -> None:
    titulo = f"{rotulo_status(relato['status'])} · {relato['protocolo']} · {relato['bairro']}"
    with st.expander(titulo, expanded=False):
        cartao_relato(relato, mostrar_descricao=True, mostrar_orientacoes=False)
        with st.form(f"status_{relato['id']}"):
            opcoes = list(STATUS)
            novo = st.selectbox("Nova situação", opcoes, index=opcoes.index(relato["status"]), format_func=rotulo_status)
            nota = st.text_area("Mensagem para o cidadão (opcional)", max_chars=300,
                                placeholder="Ex.: Equipe agendada para quinta-feira.")
            if st.form_submit_button("Salvar", type="primary"):
                try:
                    api.atualizar_status(token, relato["id"], novo, nota.strip())
                    st.toast("Situação atualizada.", icon="✅")
                    st.rerun()
                except ApiError as erro:
                    caixa_erro(erro)


def _login() -> None:
    st.markdown("### 🔐 Entrar como gestor")
    st.caption("Área restrita a servidores que tratam os relatos.")
    with st.form("login_gestor"):
        senha = st.text_input("Senha de gestor", type="password")
        entrar = st.form_submit_button("Entrar", type="primary")
    if entrar:
        if not senha:
            st.warning("Digite a senha.", icon="✍️")
            return
        try:
            session.entrar_como_gestor(api.login(senha)["token"])
            st.rerun()
        except ApiError as erro:
            caixa_erro(erro)
