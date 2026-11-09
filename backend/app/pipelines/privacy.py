"""Remove dados pessoais do relato ANTES de enviá-lo ao LLM e antes de salvar (LGPD: minimização)."""
import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_TELEFONE = re.compile(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\s?\d{4}[-\s]?\d{4}\b")


def mask_pii(texto: str) -> tuple[str, bool]:
    """Retorna (texto_mascarado, houve_remocao)."""
    original = texto
    texto = _EMAIL.sub("[e-mail removido]", texto)
    texto = _CPF.sub("[CPF removido]", texto)
    texto = _TELEFONE.sub("[telefone removido]", texto)
    return texto, texto != original
