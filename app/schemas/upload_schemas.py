from typing import List
from sqlmodel import SQLModel


class ImagenItem(SQLModel):
    url: str
    public_id: str


class UploadImagenResponse(SQLModel):
    imagen_url: str
    public_id: str
    imagenes_url: List[str] = []


class ProductoImagenesResponse(SQLModel):
    imagenes_url: List[str] = []
    imagenes: List[ImagenItem] = []
