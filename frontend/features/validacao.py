"""Validação no front ANTES do envio (o back-end valida de novo com Pydantic)."""
import re

MIN_DESCRICAO, MAX_DESCRICAO = 20, 1500


def validar_relato(descricao: str, bairro: str, cep: str, consentimento: bool) -> list[str]:
    erros = []
    d = (descricao or "").strip()
    if not d:
        erros.append("Descreva o problema que você encontrou.")
    elif len(d) < MIN_DESCRICAO:
        erros.append(f"Conte um pouco mais: a descrição precisa ter pelo menos {MIN_DESCRICAO} letras (agora tem {len(d)}).")
    elif len(d) > MAX_DESCRICAO:
        erros.append(f"A descrição pode ter no máximo {MAX_DESCRICAO} letras.")
    if len((bairro or "").strip()) < 2:
        erros.append("Informe o bairro onde está o problema.")
    if (cep or "").strip() and len(re.sub(r"\D", "", cep)) != 8:
        erros.append("O CEP deve ter 8 números (ex.: 06010-000). Se não souber, deixe em branco.")
    if not consentimento:
        erros.append("Marque a caixa confirmando que você leu como seu relato será usado.")
    return erros
