# subida de imagenes de producto a Cloudinary
# las llamadas a Cloudinary van FUERA del bloque UoW (I/O de red, no transaccion)
import asyncio
from typing import List

import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from app.core.cloudinary_setup import esta_configurado
from app.schemas.upload_schemas import (
    ImagenItem,
    ProductoImagenesResponse,
    UploadImagenResponse,
)
from app.uow import UnitOfWork

# tipos permitidos y limite de 5MB (spec v7)
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 5 * 1024 * 1024
FOLDER = "foodstore/productos"


class UploadService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def subir_imagen_producto(
        self, producto_id: int, file: UploadFile
    ) -> UploadImagenResponse:
        if not esta_configurado():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Cloudinary no configurado"
            )

        contenido = await self._leer_y_validar(file)

        with self.uow as uow:
            prod = uow.productos.get_by_id(producto_id)
            if not prod:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Producto no encontrado"
                )

        # subir fuera del UoW
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contenido,
            folder=FOLDER,
            resource_type="image",
        )
        nueva_url = result["secure_url"]
        nuevo_public_id = result["public_id"]

        # persistir: agregar al array y mantener imagen_url (primera = principal)
        with self.uow as uow:
            prod = uow.productos.get_by_id(producto_id)
            if not prod:
                await asyncio.to_thread(
                    cloudinary.uploader.destroy, nuevo_public_id, resource_type="image"
                )
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Producto no encontrado"
                )

            imagenes = list(prod.imagenes_data or [])
            imagenes.append({"url": nueva_url, "public_id": nuevo_public_id})
            prod.imagenes_data = imagenes

            # la primera imagen cargada se convierte en la principal
            if not prod.imagen_url:
                prod.imagen_url = nueva_url
                prod.imagen_public_id = nuevo_public_id

            uow.session.add(prod)

        imagenes_url = [img["url"] for img in imagenes if img.get("url")]
        return UploadImagenResponse(
            imagen_url=nueva_url,
            public_id=nuevo_public_id,
            imagenes_url=imagenes_url,
        )

    async def borrar_imagen_producto(
        self, producto_id: int, public_id: str
    ) -> None:
        with self.uow as uow:
            prod = uow.productos.get_by_id(producto_id)
            if not prod:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Producto no encontrado"
                )

            imagenes = [
                img for img in (prod.imagenes_data or [])
                if img.get("public_id") != public_id
            ]
            prod.imagenes_data = imagenes

            # si se borro la imagen principal, actualizar a la siguiente o limpiar
            if prod.imagen_public_id == public_id:
                if imagenes:
                    prod.imagen_url = imagenes[0]["url"]
                    prod.imagen_public_id = imagenes[0]["public_id"]
                else:
                    prod.imagen_url = None
                    prod.imagen_public_id = None

            uow.session.add(prod)

        # destroy fuera del UoW
        await asyncio.to_thread(
            cloudinary.uploader.destroy, public_id, resource_type="image"
        )

    def listar_imagenes_producto(
        self, producto_id: int
    ) -> ProductoImagenesResponse:
        with self.uow as uow:
            prod = uow.productos.get_by_id(producto_id)
            if not prod:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Producto no encontrado"
                )
            imagenes_raw = prod.imagenes_data or []

        imagenes = [
            ImagenItem(url=img["url"], public_id=img["public_id"])
            for img in imagenes_raw
            if img.get("url") and img.get("public_id")
        ]
        return ProductoImagenesResponse(
            imagenes_url=[img.url for img in imagenes],
            imagenes=imagenes,
        )

    @staticmethod
    async def _leer_y_validar(file: UploadFile) -> bytes:
        if file.content_type not in TIPOS_PERMITIDOS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Tipo no permitido: {file.content_type}",
            )
        contenido = await file.read()
        if len(contenido) > MAX_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "La imagen supera el limite de 5MB",
            )
        return contenido
