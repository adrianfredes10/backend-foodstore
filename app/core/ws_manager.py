# manager de conexiones WebSocket con rooms por rol y por pedido
# el broadcast se llama SIEMPRE fuera del UoW y post-commit (RN-06)
# el payload se envia plano, tal cual lo define el CONTRATO-API
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("app.ws")


class ConnectionManager:
    def __init__(self) -> None:
        # room -> set de sockets
        self.rooms: dict[str, set[WebSocket]] = {}
        # socket -> set de rooms (mapa inverso, para limpiar al desconectar)
        self.socket_rooms: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket, role: str) -> None:
        await websocket.accept()
        self._join(websocket, f"role:{role.lower()}")

    def disconnect(self, websocket: WebSocket) -> None:
        for room in self.socket_rooms.pop(websocket, set()):
            sockets = self.rooms.get(room)
            if sockets:
                sockets.discard(websocket)
                if not sockets:
                    del self.rooms[room]

    def join_order_room(self, websocket: WebSocket, pedido_id: int) -> None:
        self._join(websocket, f"order:{pedido_id}")

    def leave_order_room(self, websocket: WebSocket, pedido_id: int) -> None:
        room = f"order:{pedido_id}"
        sockets = self.rooms.get(room)
        if sockets:
            sockets.discard(websocket)
            if websocket in self.socket_rooms:
                self.socket_rooms[websocket].discard(room)
            if not sockets:
                del self.rooms[room]

    async def broadcast_to_roles(
        self, roles: list[str], payload: dict[str, Any]
    ) -> None:
        # envia a varias rooms de rol sin duplicar a un mismo socket
        enviados: set[WebSocket] = set()
        for role in roles:
            for ws in list(self.rooms.get(f"role:{role.lower()}", set())):
                if ws not in enviados:
                    await self._send(ws, payload)
                    enviados.add(ws)

    async def broadcast_to_order(
        self, pedido_id: int, payload: dict[str, Any]
    ) -> None:
        for ws in list(self.rooms.get(f"order:{pedido_id}", set())):
            await self._send(ws, payload)

    def _join(self, websocket: WebSocket, room: str) -> None:
        self.rooms.setdefault(room, set()).add(websocket)
        self.socket_rooms.setdefault(websocket, set()).add(room)

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception as e:
            logger.warning("error enviando ws, se remueve la conexion: %s", e)
            self.disconnect(websocket)


# instancia unica para toda la app
manager = ConnectionManager()
