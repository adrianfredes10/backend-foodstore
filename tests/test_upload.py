import asyncio
import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.services.upload_service import MAX_BYTES, UploadService


def _archivo(contenido: bytes, content_type: str) -> UploadFile:
    headers = Headers({"content-type": content_type})
    return UploadFile(file=io.BytesIO(contenido), filename="x", headers=headers)


def test_tipo_no_permitido_lanza_422():
    file = _archivo(b"data", "text/plain")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(UploadService._leer_y_validar(file))
    assert exc.value.status_code == 422


def test_supera_5mb_lanza_413():
    file = _archivo(b"x" * (MAX_BYTES + 1), "image/png")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(UploadService._leer_y_validar(file))
    assert exc.value.status_code == 413


def test_imagen_valida_devuelve_bytes():
    contenido = b"fake-jpeg-bytes"
    file = _archivo(contenido, "image/jpeg")
    resultado = asyncio.run(UploadService._leer_y_validar(file))
    assert resultado == contenido
