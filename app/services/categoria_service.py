from typing import List, Optional

from fastapi import HTTPException, status

from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaSimple,
    CategoriaUpdate,
)
from app.schemas.common import PaginatedResponse
from app.uow import UnitOfWork


def _to_categoria_read(categoria) -> CategoriaRead:
    subs = getattr(categoria, "subcategorias", None) or []
    activas = [s for s in subs if getattr(s, "deleted_at", None) is None]
    return CategoriaRead(
        id=categoria.id,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        parent_id=categoria.parent_id,
        activa=categoria.activa,
        created_at=categoria.created_at,
        subcategorias=[CategoriaSimple.model_validate(s) for s in activas],
    )


class CategoriaService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        parent_id: Optional[int] = None,
        activa: Optional[bool] = True,
        recursivo: bool = False,
    ) -> PaginatedResponse:
        skip = (page - 1) * size
        with self.uow as uow:
            if recursivo:
                if parent_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Con recursivo=true tenés que mandar parent_id",
                    )
                items = uow.categorias.list_subarbol_recursivo(parent_id, skip, size)
            else:
                items = uow.categorias.get_all(
                    skip=skip, limit=size, parent_id=parent_id, activa=activa
                )
            total = uow.categorias.count(activa=activa)
            pages = max(1, -(-total // size))
            return PaginatedResponse(
                items=[_to_categoria_read(c) for c in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_by_id(self, categoria_id: int) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id_con_subcategorias(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            return _to_categoria_read(categoria)

    def _validate_parent(
        self,
        uow,
        parent_id: Optional[int],
        categoria_id: Optional[int] = None,
    ) -> None:
        if parent_id is None:
            return
        parent = uow.categorias.get_by_id(parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe la categoría padre con id {parent_id}",
            )
        if categoria_id is not None:
            if not uow.categorias.validate_no_cycle(categoria_id, parent_id):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Ese padre te deja un ciclo en la jerarquía",
                )

    def create(self, categoria_data: CategoriaCreate) -> CategoriaRead:
        with self.uow as uow:
            existing = uow.categorias.get_by_nombre(categoria_data.nombre)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una categoría con ese nombre",
                )
            self._validate_parent(uow, categoria_data.parent_id)
            categoria = uow.categorias.create(categoria_data)
            uow.session.flush()
            return _to_categoria_read(categoria)

    def update(self, categoria_id: int, categoria_data: CategoriaUpdate) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            existing = uow.categorias.get_by_nombre_excluding(
                categoria_data.nombre, categoria_id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya hay otra categoría con ese nombre",
                )
            if categoria_data.parent_id is not None:
                self._validate_parent(uow, categoria_data.parent_id, categoria_id)
            categoria = uow.categorias.update(categoria, categoria_data)
            return _to_categoria_read(categoria)

    def delete(self, categoria_id: int) -> None:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            subcats = uow.categorias.get_subcategorias(categoria_id)
            if subcats:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"No se puede borrar: tiene {len(subcats)} "
                        "subcategorías activas (borralas antes)"
                    ),
                )
            if uow.categorias.has_productos(categoria_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede borrar: hay productos activos en esta categoría",
                )
            uow.categorias.soft_delete(categoria)
