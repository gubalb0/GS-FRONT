"""Tela 1 — jornada do cidadão: relatar → conferir a classificação automática (human-in-the-loop) → protocolo.

Ajustes da validação com usuários (docs/VALIDACAO.md):
- pessoa 1: mostrar ONDE registrar na prefeitura (canal oficial verificado, nunca inventado pela IA);
- pessoa 2: campo para dizer qual é o problema quando escolher "Outro"; visual com menos "cara de IA";
- pessoa 3: explicar o protocolo; destacar os telefones de emergência; "Crítica" assustava.
"""
import streamlit as st

from features.validacao import MAX_DESCRICAO, validar_relato
from providers import api_client as api
from providers.api_client import ApiError
from state import session
from ui.components import (
    badge_categoria, badge_urgencia, banner_emergencia, barra_confianca, caixa_erro, cartao_canal_oficial,
    cartao_relato, indicador_etapas, linha_de_badges, ouvir_em_voz_alta, seguro, texto_para_leitura,
)
from ui.rotulos import CATEGORIAS, ORDEM_URGENCIA, URGENCIAS, rotulo_categoria, rotulo_urgencia

# Valor-sentinela: o Streamlit trata None como "nada selecionado" e mostraria "Choose an option".
NAO_SEI = "nao_sei"
MIN_DETALHE_OUTRO, MAX_DETALHE_OUTRO = 3, 120


def render() -> None:
    etapa = st.session_state.etapa
    indicador_etapas(etapa)
    if etapa == "formulario":
        _formulario()
    elif etapa == "revisao":
        _revisao()
    else:
        _concluido()


# ---------------------------------------------------------------- etapa 1
def _formulario() -> None:
    r = st.session_state.rascunho
    st.markdown("### O que você encontrou?")
    st.caption("Escreva do seu jeito, como se estivesse contando para um vizinho. Campos com * são obrigatórios.")

    # Widgets com key=: o valor sobrevive aos reruns; ao voltar da revisão, recarregamos o rascunho.
    for campo, padrao in (("descricao", ""), ("bairro", ""), ("cidade", ""), ("cep", ""), ("categoria", NAO_SEI),
                          ("consentimento", False)):
        if f"f_{campo}" not in st.session_state:
            st.session_state[f"f_{campo}"] = r.get(campo, padrao)

    with st.form("form_relato"):
        descricao = st.text_area(
            "Descreva o problema *", key="f_descricao", max_chars=MAX_DESCRICAO, height=150,
            placeholder="Ex.: Tem um buraco grande na rua Antônio Agú, em frente ao mercado. Ontem uma moto quase caiu.",
            help="Diga o que é, onde fica (um ponto de referência ajuda) e se alguém corre risco.",
        )
        c1, c2, c3 = st.columns([2, 2, 1.4])
        bairro = c1.text_input("Bairro *", key="f_bairro", max_chars=80, placeholder="Ex.: Centro")
        cidade = c2.text_input("Cidade (opcional)", key="f_cidade", max_chars=80, placeholder="Ex.: Osasco",
                               help="Com a cidade mostramos o canal oficial certo da sua prefeitura.")
        cep = c3.text_input("CEP (opcional)", key="f_cep", max_chars=9, placeholder="00000-000",
                            help="Com o CEP completamos o endereço, a cidade e checamos a previsão de chuva.")
        categoria = st.selectbox(
            "Que tipo de problema parece ser? (opcional)", [NAO_SEI] + list(CATEGORIAS), key="f_categoria",
            format_func=lambda c: "Não sei / deixar o sistema sugerir" if c == NAO_SEI else rotulo_categoria(c),
        )
        consentimento = st.checkbox(
            "Entendi que meu relato será classificado automaticamente por inteligência artificial (IA) e que eu "
            "confiro o resultado antes de enviar. Não vou informar CPF, telefone ou e-mail (se eu informar, eles "
            "serão apagados).",
            key="f_consentimento",
        )
        enviado = st.form_submit_button("Analisar meu relato", type="primary", width="stretch")

    if not enviado:
        return

    session.guardar_rascunho(descricao=descricao, bairro=bairro, cidade=cidade, cep=cep, categoria=categoria,
                             consentimento=consentimento)
    erros = validar_relato(descricao, bairro, cep, consentimento)
    if erros:
        st.warning("**Quase lá! Ajuste estes pontos:**\n\n" + "\n".join(f"- {e}" for e in erros), icon="✍️")
        return

    with st.status("Analisando seu relato…", expanded=True) as status:
        st.write("Removendo dados pessoais do texto…")
        st.write("Consultando endereço e previsão de chuva…")
        st.write("Classificando o problema (leva alguns segundos)…")
        try:
            resultado = api.analisar(descricao.strip(), bairro.strip(), cidade.strip() or None, cep.strip() or None,
                                     None if categoria == NAO_SEI else categoria)
        except ApiError as erro:
            status.update(label="Não foi possível analisar agora", state="error", expanded=False)
            caixa_erro(erro)
            return
        status.update(label="Análise pronta!", state="complete", expanded=False)
    session.guardar_analise(resultado)
    st.rerun()


# ---------------------------------------------------------------- etapa 2
def _revisao() -> None:
    res = st.session_state.analise_atual
    if not res:
        session.novo_relato()
        st.rerun()
    a, ctx = res["analise"], res["contexto"]

    if a["urgencia"] in ("critica", "alta"):
        banner_emergencia(a["urgencia"])
    if res.get("modo") == "demonstracao":
        st.info("Modo demonstração: a classificação foi feita por regras simples, sem IA externa.", icon="🧪")
    if res.get("dados_pessoais_removidos"):
        st.warning("Encontramos dados pessoais no seu texto e eles foram apagados antes da análise.", icon="🔒")

    st.markdown("### Resumo do seu pedido")
    col_principal, col_lateral = st.columns([3, 2], gap="large")
    with col_principal:
        with st.container(border=True):
            linha_de_badges(badge_categoria(a["categoria"]), badge_urgencia(a["urgencia"]))
            st.markdown(f"**{seguro(a['resumo'])}**")
            st.caption(URGENCIAS[a["urgencia"]]["dica"])
            st.markdown("**O que você pode fazer agora:**")
            st.markdown("\n".join(f"{i}. {seguro(o)}" for i, o in enumerate(a["orientacoes"], 1)))
            st.caption(f"Setor responsável: {seguro(a['orgao_responsavel'])}")
            with st.expander("Por que o sistema sugeriu isso?"):
                st.markdown(seguro(a.get("justificativa")))
                if a.get("sinais_de_risco"):
                    st.markdown("**Sinais de risco percebidos:** " + ", ".join(seguro(s) for s in a["sinais_de_risco"]))
                st.caption("Sugestão feita por inteligência artificial — pode errar, por isso você confere abaixo.")
    with col_lateral:
        cartao_canal_oficial(res.get("canal_oficial"))
        with st.container(border=True):
            st.markdown("**Informações públicas consultadas**")
            if ctx.get("endereco"):
                st.markdown(f"📍 {seguro(ctx['endereco'])} – {seguro(ctx.get('cidade'))}/{seguro(ctx.get('uf'))}")
            if ctx.get("chuva_prevista_mm") is not None:
                icone = "⛈️" if ctx.get("alerta_chuva") else "🌤️"
                aviso = " **– alerta de chuva forte**" if ctx.get("alerta_chuva") else ""
                st.markdown(f"{icone} Chuva prevista: {ctx['chuva_prevista_mm']} mm{aviso}")
            if not ctx.get("fontes"):
                st.caption("Nenhuma fonte externa respondeu agora — a análise usou só o seu relato.")
            else:
                st.caption("Fontes: " + ", ".join(ctx["fontes"]))
            barra_confianca(a["confianca"])

    # ----- Human-in-the-loop -----
    st.markdown("### Confira antes de enviar")
    if res.get("precisa_revisao"):
        st.warning("O sistema não tem total certeza ou o caso parece grave. Revise com atenção os campos abaixo.",
                   icon="⚠️")
    else:
        st.caption("A classificação automática pode errar. Se algo não estiver certo, corrija abaixo — "
                   "sua correção ajuda a melhorar o serviço.")

    c1, c2 = st.columns(2)
    cats = list(CATEGORIAS)
    categoria_final = c1.selectbox("Tipo de problema", cats, index=cats.index(a["categoria"]),
                                   format_func=rotulo_categoria, key="hitl_categoria")
    urgencia_final = c2.selectbox("Urgência", ORDEM_URGENCIA, index=ORDEM_URGENCIA.index(a["urgencia"]),
                                  format_func=lambda u: f"{rotulo_urgencia(u)} — {URGENCIAS[u]['dica']}",
                                  key="hitl_urgencia")
    detalhe_outro = None
    if categoria_final == "outro":
        detalhe_outro = st.text_input(
            "Qual é o problema? *", key="hitl_detalhe_outro", max_chars=MAX_DETALHE_OUTRO,
            placeholder="Ex.: Pichação no muro da escola, banco da praça quebrado…",
            help="Como o problema não se encaixa nas opções, conte em poucas palavras o que é.",
        ).strip()
    if categoria_final != a["categoria"] or urgencia_final != a["urgencia"]:
        st.caption("✏️ Você alterou a sugestão automática. Vamos registrar a sua versão.")

    b1, b2 = st.columns(2)
    if b1.button("Confirmar e registrar", type="primary", width="stretch"):
        if categoria_final == "outro" and len(detalhe_outro or "") < MIN_DETALHE_OUTRO:
            st.warning("Escreva em poucas palavras qual é o problema no campo **Qual é o problema?**", icon="✍️")
            return
        with st.spinner("Registrando seu relato…"):
            try:
                relato = api.confirmar(res["analise_id"], categoria_final, urgencia_final, detalhe_outro)
            except ApiError as erro:
                caixa_erro(erro)
                if erro.codigo == "analise_nao_encontrada":
                    session.ir_para("formulario")
                return
        session.registrar_relato(relato)
        st.rerun()
    if b2.button("Voltar e editar o texto", width="stretch"):
        session.ir_para("formulario")
        st.rerun()


# ---------------------------------------------------------------- etapa 3
def _concluido() -> None:
    relato = st.session_state.ultimo_relato
    if not relato:
        session.novo_relato()
        st.rerun()
    st.success(f"**Relato registrado!** Seu número de protocolo é **{relato['protocolo']}**", icon="✅")
    with st.container(border=True):
        st.markdown("**O que é o protocolo?**")
        st.markdown(
            "É o número do seu pedido aqui no Zelo. Com ele você acompanha a situação na aba **Meus relatos** "
            "e vê quando a equipe responder. **Anote o número ou tire um print desta tela.**"
        )
    if relato["urgencia"] in ("critica", "alta"):
        banner_emergencia(relato["urgencia"])

    col_relato, col_canal = st.columns([3, 2], gap="large")
    with col_relato:
        cartao_relato(relato, mostrar_descricao=False)
        ouvir_em_voz_alta(texto_para_leitura(relato))
    with col_canal:
        st.info("**Próximo passo:** o Zelo ainda não envia pedidos automaticamente para a prefeitura. "
                "Para garantir o atendimento, registre também no canal oficial abaixo.", icon="ℹ️")
        resumo = relato["resumo"]
        if relato.get("detalhe_outro"):
            resumo = f"{relato['detalhe_outro']}. {resumo}"
        cartao_canal_oficial(relato.get("canal_oficial"),
                             resumo=f"{resumo} Bairro: {relato['bairro']}. Protocolo Zelo: {relato['protocolo']}.")
    if st.button("Fazer outro relato", type="primary"):
        session.novo_relato()
        st.rerun()
