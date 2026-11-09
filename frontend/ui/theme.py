"""Estilos globais: identidade visual, foco visível para teclado, alto contraste e fonte maior."""
import streamlit as st

BASE = """
<style>
  .zelo-badge {display:inline-block;padding:3px 10px;margin:2px 4px 2px 0;border-radius:999px;
               font-size:0.88rem;font-weight:600;border:1px solid rgba(0,0,0,.08)}
  .zelo-step {padding:4px 10px;border-radius:8px;color:inherit;opacity:.8;font-weight:500}
  .zelo-step-on {background:#0B6E4F;color:#fff !important;opacity:1;font-weight:700}
  .zelo-empty {text-align:center;padding:32px 16px;border:2px dashed #94A3B8;border-radius:14px;color:inherit}
  .zelo-empty-icon {font-size:2.4rem;margin-bottom:6px}
  .zelo-hero {background:linear-gradient(120deg,#0B6E4F 0%,#14532D 100%);color:#fff;padding:22px 26px;
              border-radius:16px;margin-bottom:14px}
  .zelo-hero h1 {color:#fff;margin:0;font-size:2rem}
  .zelo-hero p {color:#E7F5EF;margin:6px 0 0 0;font-size:1.05rem}
  /* foco sempre visível para quem navega com teclado */
  *:focus-visible {outline:3px solid #1D4ED8 !important;outline-offset:2px !important}
</style>
"""

ALTO_CONTRASTE = """
<style>
  .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] {background:#000 !important}
  .stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
  .stApp div[data-testid="stMarkdownContainer"], .stApp small {color:#fff !important}
  .stApp textarea, .stApp input, .stApp [data-baseweb="select"] > div
      {background:#000 !important;color:#fff !important;border:2px solid #fff !important}
  .stApp [data-baseweb="select"] > div * {background:transparent !important;color:#fff !important}
  .stApp [data-baseweb="select"] svg {fill:#fff !important}
  .stApp [data-testid^="stBaseButton"] {border:2px solid #FFD400 !important}
  .stApp textarea::placeholder, .stApp input::placeholder {color:#C7C7C7 !important;opacity:1 !important}
  .stApp a {color:#FFD400 !important}
  .zelo-badge {background:#000 !important;color:#fff !important;border:2px solid #fff !important}
  .zelo-step-on {background:#FFD400 !important;color:#000 !important}
  .zelo-hero {background:#000 !important;border:2px solid #FFD400}
  [data-testid="stVerticalBlockBorderWrapper"] {border-color:#fff !important}
  /* caixas de aviso (sucesso, erro, info, alerta): fundo preto e borda colorida */
  .stApp [data-testid="stAlertContainer"] {background:#000 !important;border:2px solid #fff !important}
  .stApp [data-testid="stAlertContainer"] * {color:#fff !important}
  /* botões secundários e caixas de seleção abertas */
  .stApp button[kind="secondary"], .stApp button[kind="secondaryFormSubmit"],
  .stApp [data-testid="stBaseButton-secondary"], .stApp [data-testid="stBaseButton-secondaryFormSubmit"]
      {background:#000 !important;color:#fff !important}
  [data-baseweb="popover"] ul, [data-baseweb="popover"] li {background:#000 !important;color:#fff !important}
  [data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"]
      {background:#333 !important}
  .stApp [data-testid="stExpander"] details, .stApp [data-testid="stExpander"] summary
      {background:#000 !important;border-color:#fff !important}
  *:focus-visible {outline:3px solid #FFD400 !important}
</style>
"""

FONTE_GRANDE = "<style>html, .stApp {font-size:19px !important} .stApp p, .stApp li, .stApp label {font-size:1.12rem !important}</style>"


def aplicar_tema(alto_contraste: bool, fonte_grande: bool) -> None:
    css = BASE + (ALTO_CONTRASTE if alto_contraste else "") + (FONTE_GRANDE if fonte_grande else "")
    st.markdown(css, unsafe_allow_html=True)
