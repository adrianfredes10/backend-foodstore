# endpoint WebSocket del feed de staff (ADMIN/PEDIDOS)
# auth por cookie HttpOnly (igual que la auth REST)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import ExpiredSignatureError, JWTError
from sqlmodel import Session, select

from app.constants.codigos import RolCodigo
from app.core.security import decode_access_token
from app.core.ws_manager import manager
from app.database import engine
from app.models.seguridad import Usuario

router = APIRouter()

# close codes (alineados al CONTRATO-API)
WS_TOKEN_EXPIRADO = 4001  # el front refresca y reconecta
WS_NO_AUTORIZADO = 1008   # sin sesion / token invalido / rol no permitido

STAFF_WS = (RolCodigo.ADMIN, RolCodigo.PEDIDOS)


@router.websocket("/ws/pedidos")
async def ws_pedidos(websocket: WebSocket):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.accept()
        await websocket.close(code=WS_NO_AUTORIZADO, reason="No autenticado")
        return

    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        await websocket.accept()
        await websocket.close(code=WS_TOKEN_EXPIRADO, reason="Token expirado")
        return
    except JWTError:
        await websocket.accept()
        await websocket.close(code=WS_NO_AUTORIZADO, reason="Token invalido")
        return

    uid = payload.get("uid")
    if not uid:
        await websocket.accept()
        await websocket.close(code=WS_NO_AUTORIZADO, reason="Token invalido")
        return

    # validar usuario y rol contra la base (datos frescos)
    with Session(engine) as session:
        user = session.exec(
            select(Usuario).where(
                Usuario.id == int(uid), Usuario.deleted_at.is_(None)
            )
        ).first()
        if not user or not user.activo:
            await websocket.accept()
            await websocket.close(code=WS_NO_AUTORIZADO, reason="Usuario invalido")
            return
        roles = {r.codigo for r in user.roles}

    rol_room = next((r for r in STAFF_WS if r in roles), None)
    if not rol_room:
        await websocket.accept()
        await websocket.close(code=WS_NO_AUTORIZADO, reason="Rol no autorizado")
        return

    await manager.connect(websocket, role=rol_room)
    try:
        # el feed staff es de solo lectura; el receive mantiene viva la conexion
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
