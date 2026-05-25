from typing import List

from fastapi import HTTPException, status

from app.models.direccion_entrega import DireccionEntrega
from app.schemas.direccion_schemas import DireccionCreate, DireccionRead, DireccionUpdate
from app.uow import UnitOfWork


class DireccionService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @staticmethod
    def _read(d: DireccionEntrega) -> DireccionRead:
        return DireccionRead(
            id=d.id,
            usuario_id=d.usuario_id,
            alias=d.alias,
            calle=d.calle,
            numero=d.numero,
            referencia=d.referencia,
            ciudad=d.ciudad,
            codigo_postal=d.codigo_postal,
            es_principal=d.es_principal,
            created_at=d.created_at,
        )

    def obtener(self, usuario_id: int, direccion_id: int) -> DireccionRead:
        with self.uow as uow:
            d = uow.direcciones.get_owned(direccion_id, usuario_id)
            if not d:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            return self._read(d)

    def listar(self, usuario_id: int) -> List[DireccionRead]:
        with self.uow as uow:
            rows = uow.direcciones.list_by_usuario(usuario_id)
            return [self._read(d) for d in rows]

    def crear(self, usuario_id: int, data: DireccionCreate) -> DireccionRead:
        with self.uow as uow:
            existentes = uow.direcciones.list_by_usuario(usuario_id)
            es_principal = data.es_principal or len(existentes) == 0
            if es_principal:
                uow.direcciones.clear_principal_usuario(usuario_id)
            row = DireccionEntrega(
                usuario_id=usuario_id,
                alias=data.alias,
                calle=data.calle,
                numero=data.numero,
                referencia=data.referencia,
                ciudad=data.ciudad,
                codigo_postal=data.codigo_postal,
                es_principal=es_principal,
            )
            uow.direcciones.create(row)
            uow.flush()
            return self._read(row)

    def actualizar(
        self, usuario_id: int, direccion_id: int, data: DireccionUpdate
    ) -> DireccionRead:
        with self.uow as uow:
            d = uow.direcciones.get_owned(direccion_id, usuario_id)
            if not d:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            patch = data.model_dump(exclude_unset=True)
            if not patch:
                return self._read(d)
            uow.direcciones.update_fields(d, **patch)
            uow.flush()
            uow.refresh(d)
            return self._read(d)

    def eliminar(self, usuario_id: int, direccion_id: int) -> None:
        with self.uow as uow:
            d = uow.direcciones.get_owned(direccion_id, usuario_id)
            if not d:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            era_principal = d.es_principal
            otros = [
                x
                for x in uow.direcciones.list_by_usuario(usuario_id)
                if x.id != direccion_id
            ]
            uow.direcciones.soft_delete(d)
            if era_principal and otros:
                uow.direcciones.clear_principal_usuario(usuario_id)
                primero = otros[0]
                primero.es_principal = True
                uow.session.add(primero)

    def marcar_principal(self, usuario_id: int, direccion_id: int) -> DireccionRead:
        with self.uow as uow:
            d = uow.direcciones.get_owned(direccion_id, usuario_id)
            if not d:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            uow.direcciones.clear_principal_usuario(usuario_id)
            d.es_principal = True
            uow.session.add(d)
            uow.flush()
            uow.refresh(d)
            return self._read(d)
