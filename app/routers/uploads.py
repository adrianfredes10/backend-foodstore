from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile, status

from app.constants.codigos import RolCodigo
from app.core.auth_deps import require_roles
from app.models.seguridad import Usuario
from app.schemas.upload_schemas import UploadImagenResponse
from app.services.upload_service import UploadService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["uploads"])


# endpoints spec v6: genericos (no asociados a producto)
# el frontend sube, obtiene la URL y la asocia al producto por separado

@router.post("/imagen", response_model=UploadImagenResponse, status_code=201)
async def subir_imagen(
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    file: Annotated[UploadFile, File()],
    uow: UnitOfWork = Depends(get_uow),
):
    return await UploadService(uow).subir_imagen_generica(file)


@router.delete("/imagen/{public_id:path}", status_code=status.HTTP_204_NO_CONTENT)
async def borrar_imagen(
    public_id: str,
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    await UploadService(uow).borrar_imagen_generica(public_id)


@router.post("/producto/{producto_id}/imagen", response_model=UploadImagenResponse)
async def subir_imagen_producto(
    producto_id: Annotated[int, Path(gt=0)],
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    file: Annotated[UploadFile, File()],
    uow: UnitOfWork = Depends(get_uow),
):
    return await UploadService(uow).subir_imagen_producto(producto_id, file)


@router.delete(
    "/producto/{producto_id}/imagen/{public_id:path}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def borrar_imagen_producto(
    producto_id: Annotated[int, Path(gt=0)],
    public_id: str,
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    await UploadService(uow).borrar_imagen_producto(producto_id, public_id)
