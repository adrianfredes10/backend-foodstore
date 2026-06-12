# endpoint WebSocket de pedidos: staff (ADMIN/PEDIDOS) y clientes (CLIENT)
# auth por cookie HttpOnly (igual que la auth REST)
# staff recibe todos los cambios via room role:{rol}; el cliente se suscribe
# a sus pedidos con {"action": "subscribe-order", "order_id": N} (CONTRATO-API)
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import ExpiredSignatureError, JWTError
from sqlmodel import Session, select

from app.constants.codigos import RolCodigo
from app.core.security import decode_access_token
from app.core.ws_manager import manager
from app.database import engine
from app.models.pedido import Pedido
from app.models.seguridad import Usuario

router = APIRouter()

# close codes (alineados al CONTRATO-API)
WS_TOKEN_EXPIRADO = 4001  # el front refresca y reconecta
WS_NO_AUTORIZADO = 1008   # sin sesion / token invalido / rol no permitido

STAFF_WS = (RolCodigo.ADMIN, RolCodigo.PEDIDOS)


def _puede_suscribirse(pedido_id: int, usuario_id: int, es_staff: bool) -> bool:
    # el cliente solo puede suscribirse a sus propios pedidos
    with Session(engine) as session:
        pedido = session.get(Pedido, pedido_id)
        if not pedido:
            return False
        return es_staff or pedido.usuario_id == usuario_id


@router.websocket("/api/v1/ws")
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
    es_staff = rol_room is not None
    if not es_staff and RolCodigo.CLIENT not in roles:
        await websocket.accept()
        await websocket.close(code=WS_NO_AUTORIZADO, reason="Rol no autorizado")
        return

    # staff entra a su room de rol; el cliente conecta sin room inicial
    await manager.connect(websocket, role=rol_room)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("action") == "subscribe-order":
                order_id = msg.get("order_id")
                if isinstance(order_id, int) and _puede_suscribirse(
                    order_id, int(uid), es_staff
                ):
                    manager.join_order_room(websocket, order_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
