# SDK de MercadoPago configurado desde .env (mismo patron que cloudinary_setup)
# el ACCESS_TOKEN es sensible: solo en .env local, nunca en el repo ni el frontend
import mercadopago

from app.core.config import get_settings


def esta_configurado() -> bool:
    return bool(get_settings().MERCADOPAGO_ACCESS_TOKEN)


def get_sdk() -> mercadopago.SDK:
    return mercadopago.SDK(get_settings().MERCADOPAGO_ACCESS_TOKEN)
