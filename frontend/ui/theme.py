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
  /* Cabeçalho sóbrio, de serviço público (pessoa 2 achou o visual com "cara de IA") */
  .zelo-hero {border-top:6px solid #0B6E4F;border-bottom:1px solid #D7DEDB;padding:14px 2px 16px;margin-bottom:10px}
  .zelo-hero h1 {margin:0;font-size:1.9rem;font-weight:700;letter-spacing:-.01em}
  .zelo-hero .zelo-marca {color:#0B6E4F}
  .zelo-hero p {margin:4px 0 0 0;font-size:1.05rem;opacity:.85}
  /* Emergência: números grandes, a um toque no celular */
  .zelo-emergencia {border:2px solid #B91C1C;border-left-width:8px;border-radius:10px;padding:14px 16px;margin:6px 0 14px;
                    background:#FEF2F2;color:#450A0A}
  .zelo-emergencia p {margin:0 0 10px 0;color:#450A0A}
  .zelo-tels {display:flex;flex-wrap:wrap;gap:8px}
  .zelo-tel {display:inline-flex;align-items:baseline;gap:6px;padding:8px 14px;border-radius:8px;background:#B91C1C;
             color:#fff !important;text-decoration:none !important;font-size:1rem}
  .zelo-tel strong {font-size:1.25rem}
  .zelo-tel:hover {background:#7F1D1D}
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
  .zelo-hero {background:#000 !important;border-top-color:#FFD400 !important}
  .zelo-hero .zelo-marca {color:#FFD400 !important}
  .zelo-emergencia {background:#000 !important;border-color:#FF6B6B !important}
  .zelo-emergencia p, .zelo-emergencia strong {color:#fff !important}
  .stApp a.zelo-tel {background:#FFD400 !important;color:#000 !important}
  .stApp a.zelo-tel strong {color:#000 !important}
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
