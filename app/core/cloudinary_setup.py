# configuracion de Cloudinary desde settings (credenciales en .env)
import cloudinary

from app.core.config import get_settings

_s = get_settings()

cloudinary.config(
    cloud_name=_s.CLOUDINARY_CLOUD_NAME,
    api_key=_s.CLOUDINARY_API_KEY,
    api_secret=_s.CLOUDINARY_API_SECRET,
    secure=True,
)


def esta_configurado() -> bool:
    return bool(
        _s.CLOUDINARY_CLOUD_NAME
        and _s.CLOUDINARY_API_KEY
        and _s.CLOUDINARY_API_SECRET
    )
