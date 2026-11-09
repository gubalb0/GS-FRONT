"""Autenticação simples do perfil gestor (token assinado com HMAC e expiração)."""
import hashlib
import hmac
import time


def _assinar(segredo: str, exp: int) -> str:
    return hmac.new(segredo.encode(), f"gestor:{exp}".encode(), hashlib.sha256).hexdigest()


def create_token(segredo: str, ttl_minutes: int) -> tuple[str, int]:
    exp = int(time.time()) + ttl_minutes * 60
    return f"{exp}.{_assinar(segredo, exp)}", exp


def verify_token(token: str, segredo: str) -> bool:
    try:
        exp_txt, assinatura = token.split(".", 1)
        exp = int(exp_txt)
    except ValueError:
        return False
    if exp < time.time():
        return False
    return hmac.compare_digest(assinatura, _assinar(segredo, exp))


def check_password(informada: str, esperada: str) -> bool:
    return hmac.compare_digest(informada.encode(), esperada.encode())
