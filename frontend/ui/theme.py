"""Estilos globais: identidade visual, foco visível para teclado, alto contraste e fonte maior."""
import streamlit as st

BASE = """
<style>
  .zelo-badge {display:inline-block;padding:3px 10px;margin:2px 4px 2px 0;border-radius:999px;
               font-size:0.88rem;font-weight:600;border:1px solid rgba(0,0,0,.08)}
  .zelo-step {padding:4px 10px;border-radius:8px;color:#475569;font-weight:500}
  .zelo-step-on {background:#0B6E4F;color:#fff !important;font-weight:700}
  .zelo-empty {text-align:center;padding:32px 16px;border:2px dashed #CBD5E1;border-radius:14px;color:#334155}
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
  .stApp button {border:2px solid #FFD400 !important}
  .stApp a {color:#FFD400 !important}
  .zelo-badge {background:#000 !important;color:#fff !important;border:2px solid #fff !important}
  .zelo-step-on {background:#FFD400 !important;color:#000 !important}
  .zelo-hero {background:#000 !important;border:2px solid #FFD400}
  [data-testid="stVerticalBlockBorderWrapper"] {border-color:#fff !important}
  *:focus-visible {outline:3px solid #FFD400 !important}
</style>
"""

FONTE_GRANDE = "<style>html, .stApp {font-size:19px !important} .stApp p, .stApp li, .stApp label {font-size:1.12rem !important}</style>"


def aplicar_tema(alto_contraste: bool, fonte_grande: bool) -> None:
    css = BASE + (ALTO_CONTRASTE if alto_contraste else "") + (FONTE_GRANDE if fonte_grande else "")
    st.markdown(css, unsafe_allow_html=True)
