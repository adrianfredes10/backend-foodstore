from typing import List, Optional
from sqlmodel import SQLModel


class ImagenItem(SQLModel):
    url: str
    public_id: str


class UploadImagenResponse(SQLModel):
    imagen_url: str
    public_id: str
    imagenes_url: List[str] = []
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    resource_type: Optional[str] = None


class ProductoSetImagenesBody(SQLModel):
    # lista de URLs a conservar; se descartan las que no esten en la lista
    imagenes_url: List[str]


class ProductoImagenesResponse(SQLModel):
    imagenes_url: List[str] = []
    imagenes: List[ImagenItem] = []
