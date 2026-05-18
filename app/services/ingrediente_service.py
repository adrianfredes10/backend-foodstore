from typing import List
from fastapi import HTTPException, status
from app.uow import UnitOfWork
from app.schemas.ingrediente import IngredienteCreate, IngredienteUpdate, IngredienteRead


class IngredienteService:
    """Orquesta la lógica de negocio de ingredientes usando UnitOfWork. Sin SQL directo, sin commit."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all(self, skip: int = 0, limit: int = 100) -> List[IngredienteRead]:
        with self.uow as uow:
            items = uow.ingredientes.get_all(skip=skip, limit=limit)
            return [IngredienteRead.model_validate(i) for i in items]

    def get_by_id(self, ingrediente_id: int) -> IngredienteRead:
        with self.uow as uow:
            ingrediente = uow.ingredientes.get_by_id(ingrediente_id)
            if not ingrediente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ingrediente no encontrado"
                )
            return IngredienteRead.model_validate(ingrediente)

    def create(self, ingrediente_data: IngredienteCreate) -> IngredienteRead:
        with self.uow as uow:
            existing = uow.ingredientes.get_by_nombre(ingrediente_data.nombre)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ingrediente ya existe"
                )
            ingrediente = uow.ingredientes.create(ingrediente_data)
            uow.session.flush()
            return IngredienteRead.model_validate(ingrediente)

    def update(self, ingrediente_id: int, ingrediente_data: IngredienteUpdate) -> IngredienteRead:
        with self.uow as uow:
            ingrediente = uow.ingredientes.get_by_id(ingrediente_id)
            if not ingrediente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ingrediente no encontrado"
                )
            existing = uow.ingredientes.get_by_nombre_excluding(ingrediente_data.nombre, ingrediente_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro ingrediente con ese nombre"
                )
            ingrediente = uow.ingredientes.update(ingrediente, ingrediente_data)
            return IngredienteRead.model_validate(ingrediente)

    def delete(self, ingrediente_id: int) -> None:
        with self.uow as uow:
            ingrediente = uow.ingredientes.get_by_id(ingrediente_id)
            if not ingrediente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ingrediente no encontrado"
                )
            if uow.ingredientes.has_productos(ingrediente_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede eliminar el ingrediente porque tiene productos relacionados"
                )
            uow.ingredientes.soft_delete(ingrediente)
