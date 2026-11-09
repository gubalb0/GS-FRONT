"""Componentes visuais reutilizáveis. Todo texto vindo do usuário passa por `seguro()` antes de virar HTML."""
import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from ui.rotulos import CATEGORIAS, STATUS, URGENCIAS, rotulo_categoria, rotulo_urgencia


def seguro(texto: str | None) -> str:
    """Escapa HTML e Markdown para exibir texto do cidadão sem risco de injeção."""
    texto = html.escape(texto or "")
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~])", r"\\\1", texto)


def _badge(icone: str, texto: str, fg: str, bg: str, titulo: str = "") -> str:
    return (f'<span class="zelo-badge" style="color:{fg};background:{bg}" title="{html.escape(titulo)}">'
            f'<span aria-hidden="true">{icone}</span> {html.escape(texto)}</span>')


def badge_urgencia(urg: str) -> str:
    u = URGENCIAS[urg]
    return _badge(u["icone"], f"Urgência {u['rotulo']}", u["fg"], u["bg"], u["dica"])


def badge_categoria(cat: str) -> str:
    icone, texto = CATEGORIAS.get(cat, ("📌", cat))
    return _badge(icone, texto, "#1E293B", "#E2E8F0")


def badge_status(status: str) -> str:
    icone, texto = STATUS.get(status, ("•", status))
    return _badge(icone, texto, "#1E3A8A", "#DBEAFE")


def linha_de_badges(*badges: str) -> None:
    st.markdown(" ".join(badges), unsafe_allow_html=True)


def indicador_etapas(atual: str) -> None:
    etapas = [("formulario", "1. Conte o problema"), ("revisao", "2. Confira a análise"), ("concluido", "3. Protocolo")]
    partes = []
    for chave, rotulo in etapas:
        if chave == atual:
            partes.append(f'<span class="zelo-step zelo-step-on" aria-current="step">{rotulo}</span>')
        else:
            partes.append(f'<span class="zelo-step">{rotulo}</span>')
    st.markdown('<nav aria-label="Etapas do relato">' + ' <span aria-hidden="true">→</span> '.join(partes) + "</nav>",
                unsafe_allow_html=True)


def estado_vazio(icone: str, titulo: str, mensagem: str) -> None:
    st.markdown(
        f'<div class="zelo-empty" role="status"><div class="zelo-empty-icon" aria-hidden="true">{icone}</div>'
        f"<strong>{html.escape(titulo)}</strong><p>{html.escape(mensagem)}</p></div>",
        unsafe_allow_html=True,
    )


def caixa_erro(erro) -> None:
    """Mensagem amigável para qualquer ApiError."""
    st.error(f"**Não deu certo desta vez.** {erro.mensagem}", icon="⚠️")
    for campo in erro.campos:
        st.markdown(f"- {campo}")
    if erro.codigo in ("offline", "timeout", "ia_indisponivel", "ia_timeout", "ia_ocupada"):
        st.caption("Seu texto continua salvo no formulário — é só tentar de novo.")


def banner_emergencia() -> None:
    st.error("**🚨 Existe risco imediato?** Não espere o protocolo: ligue **199** (Defesa Civil), "
             "**193** (Bombeiros) ou **192** (SAMU).", icon="🚨")


def barra_confianca(confianca: float) -> None:
    nivel = "alta" if confianca >= 0.75 else "média" if confianca >= 0.6 else "baixa"
    st.progress(min(max(confianca, 0.0), 1.0), text=f"Certeza da IA: {nivel} ({confianca:.0%})")


def ouvir_em_voz_alta(texto: str, rotulo: str = "🔊 Ouvir em voz alta") -> None:
    """Leitura em voz alta pelo próprio navegador (Web Speech API, pt-BR)."""
    # "<" vira \u003c: o texto (que inclui saída do LLM) nunca consegue fechar a tag <script>.
    texto_js = json.dumps(texto).replace("<", "\\u003c")
    conteudo = (
        f"""<button id="falar" aria-label="{html.escape(rotulo)}"
            style="font:600 15px sans-serif;padding:8px 14px;border-radius:8px;border:2px solid #0B6E4F;
                   background:#fff;color:#0B6E4F;cursor:pointer">{html.escape(rotulo)}</button>
        <script>
          const b = document.getElementById('falar');
          b.onclick = () => {{
            if (!('speechSynthesis' in window)) {{ b.innerText = 'Seu navegador não lê em voz alta'; return; }}
            const u = new SpeechSynthesisUtterance({texto_js}); u.lang = 'pt-BR';
            window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
          }};
        </script>"""
    )
    if hasattr(st, "iframe"):  # Streamlit >= 1.5x
        st.iframe(conteudo, height=52)
    else:
        components.html(conteudo, height=52)


def texto_para_leitura(relato: dict) -> str:
    passos = ". ".join(relato.get("orientacoes", []))
    return (f"Protocolo {' '.join(relato.get('protocolo', ''))}. {relato.get('resumo', '')} "
            f"Urgência {URGENCIAS[relato['urgencia']]['rotulo']}. O que você pode fazer agora: {passos}")


def cartao_relato(relato: dict, *, mostrar_descricao: bool = True, mostrar_orientacoes: bool = True) -> None:
    """Cartão de um relato — usado na confirmação, em 'Meus relatos' e na fila do gestor."""
    with st.container(border=True):
        topo, data = st.columns([3, 2])
        topo.markdown(f"**Protocolo `{relato.get('protocolo', '—')}`**")
        if relato.get("criado_em"):
            data.caption(f"🕒 {str(relato['criado_em'])[:16].replace('T', ' ')} · 📍 {seguro(relato.get('bairro'))}")
        linha_de_badges(badge_categoria(relato["categoria"]), badge_urgencia(relato["urgencia"]),
                        badge_status(relato.get("status", "recebido")))
        st.markdown(seguro(relato.get("resumo")))
        if relato.get("corrigido_pelo_cidadao"):
            st.caption(f"✏️ Corrigido pelo cidadão. A IA havia sugerido: {rotulo_categoria(relato['categoria_ia'])} · "
                       f"{rotulo_urgencia(relato['urgencia_ia'])}")
        if mostrar_orientacoes and relato.get("orientacoes"):
            st.markdown("**O que fazer agora:**")
            st.markdown("\n".join(f"{i}. {seguro(o)}" for i, o in enumerate(relato["orientacoes"], 1)))
        st.caption(f"🏛️ Encaminhar para: {seguro(relato.get('orgao_responsavel'))}")
        if relato.get("nota_gestor"):
            st.info(f"💬 Resposta da prefeitura: {seguro(relato['nota_gestor'])}")
        if mostrar_descricao and relato.get("descricao"):
            with st.expander("Ver relato original"):
                st.markdown(seguro(relato["descricao"]))
