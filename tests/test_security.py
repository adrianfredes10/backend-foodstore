# tests de seguridad (hash de password y refresh token, sin base de datos)
from app.core.security import (
    generar_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_password_verifica_ok():
    h = hash_password("Secreta123!")
    assert h != "Secreta123!"
    assert verify_password("Secreta123!", h)
    assert not verify_password("otra", h)


def test_refresh_token_es_aleatorio():
    a = generar_refresh_token()
    b = generar_refresh_token()
    assert a != b
    assert len(a) > 30


def test_hash_refresh_es_estable_y_distinto_del_plano():
    plano = generar_refresh_token()
    h1 = hash_refresh_token(plano)
    h2 = hash_refresh_token(plano)
    assert h1 == h2
    assert h1 != plano
    # sha256 hex = 64 chars
    assert len(h1) == 64
