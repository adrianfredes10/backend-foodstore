# Documentación de rutas — Food Store API

Base URL en desarrollo: `http://localhost:8000`

Documentación interactiva: **`GET /docs`** (Swagger) y **`GET /redoc`**.

---

## Autenticación (JWT)

- **Login** (`POST /api/v1/auth/login`) recibe JSON `{"email": "...", "password": "..."}`, devuelve `UsuarioPublic` y setea una **cookie HttpOnly** llamada `access_token` con el JWT.
- **JWT:** firmado con **python-jose** (HS256).
- **Vencimiento:** `ACCESS_TOKEN_EXPIRE_MINUTES` (por defecto 30 min en `app/core/config.py`).
- **Clave secreta:** variable de entorno `SECRET_KEY`.
- Las rutas protegidas leen el JWT desde la **cookie** (`COOKIE_NAME = "access_token"` en `app/deps/auth_deps.py`).
- El front debe enviar cookies: `credentials: "include"` en fetch o `withCredentials: true` en Axios.

---

## Códigos de rol

Definidos en `app/constants/codigos.py`:

| Código | Uso |
|--------|-----|
| `ADMIN` | ABM completo, panel admin, cambio de estado de pedidos |
| `STOCK` | Stock y disponibilidad de productos |
| `PEDIDOS` | Cambio de estado de pedidos (junto con ADMIN) |
| `CLIENT` | Cliente registrado (se asigna al registrarse) |

---

## Resumen por prefijo

| Prefijo | Auth requerida |
|---------|----------------|
| `/api/v1/auth` | Público salvo `/me` |
| `/api/v1/categorias` | GET público; escritura requiere **ADMIN** |
| `/api/v1/ingredientes` | GET público; escritura requiere **ADMIN** |
| `/api/v1/productos` | GET público; escritura según ruta |
| `/api/v1/direcciones` | Todas requieren usuario logueado |
| `/api/v1/pedidos` | Todas requieren usuario logueado |
| `/api/v1/admin` | Solo **ADMIN** |
| `/api/v1/formas-pago` | Público |
| `/api/v1/estados-pedido` | Público |

---

## Rutas detalladas

### Raíz

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Metadatos de la API + enlace a `/docs` |

---

### `/api/v1/auth`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Registro. Body JSON: `email`, `password` (min 8), `nombre`, `apellido`, `telefono` (opcional). Responde 201 con `UsuarioPublic`. |
| POST | `/api/v1/auth/login` | No | Login. Body JSON: `email`, `password`. Responde 200 con `UsuarioPublic` y setea cookie `access_token`. |
| POST | `/api/v1/auth/logout` | No | Borra la cookie `access_token`. Responde 204. |
| GET | `/api/v1/auth/me` | Sí (cookie) | Perfil del usuario actual con roles. Responde `UsuarioPublic`. |

**`UsuarioPublic`:**
```json
{
  "id": 1,
  "email": "user@ejemplo.com",
  "nombre": "Juan",
  "apellido": "Perez",
  "telefono": null,
  "activo": true,
  "roles": [{ "id": 1, "codigo": "CLIENT", "nombre": "Cliente" }]
}
```

---

### `/api/v1/categorias`

| Método | Ruta | Auth | Query params |
|--------|------|------|--------------|
| GET | `/api/v1/categorias` | No | `page` (1), `size` (20), `parent_id`, `activa` (true), `recursivo` (false). Responde `PaginatedResponse`. |
| GET | `/api/v1/categorias/{id}` | No | Detalle con subcategorías. |
| POST | `/api/v1/categorias` | **ADMIN** | Body: `nombre`, `descripcion`, `parent_id`. |
| PUT | `/api/v1/categorias/{id}` | **ADMIN** | Actualizar. |
| DELETE | `/api/v1/categorias/{id}` | **ADMIN** | Soft delete. Falla 409 si tiene productos activos. |

---

### `/api/v1/ingredientes`

| Método | Ruta | Auth | Notas |
|--------|------|------|-------|
| GET | `/api/v1/ingredientes` | No | `skip`, `limit` |
| GET | `/api/v1/ingredientes/{id}` | No | |
| POST | `/api/v1/ingredientes` | **ADMIN** | Body incluye `descripcion`, `es_alergeno` |
| PUT | `/api/v1/ingredientes/{id}` | **ADMIN** | |
| DELETE | `/api/v1/ingredientes/{id}` | **ADMIN** | Soft delete |

---

### `/api/v1/productos`

| Método | Ruta | Auth | Notas |
|--------|------|------|-------|
| GET | `/api/v1/productos` | No | `page`, `size`, `categoria_id`, `disponible`, `q` (búsqueda por nombre). Responde `PaginatedResponse`. |
| GET | `/api/v1/productos/{id}` | No | Detalle con categoría e ingredientes. `precio` se devuelve como **string**. |
| POST | `/api/v1/productos` | **ADMIN** | Body: `nombre`, `descripcion`, `precio`, `disponible`, `stock_cantidad`, `imagen_url`, `categoria_id`, `ingredientes[]`. |
| PUT | `/api/v1/productos/{id}` | **ADMIN** | Actualizar completo. |
| DELETE | `/api/v1/productos/{id}` | **ADMIN** | Soft delete. |
| PATCH | `/api/v1/productos/{id}/stock` | **ADMIN** o **STOCK** | Body: `{"stock_cantidad": 100}` |
| PATCH | `/api/v1/productos/{id}/disponibilidad` | **ADMIN** o **STOCK** | Body: `{"disponible": true}` |

**`ProductoRead`:** incluye `categoria` como objeto (no ID), `precio` como string para evitar problemas de precisión en JS.

---

### `/api/v1/direcciones`

Todas requieren **usuario autenticado** (cookie JWT).

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/direcciones` | Listado de direcciones del usuario. |
| GET | `/api/v1/direcciones/{direccion_id}` | Detalle de una dirección propia. 404 si no existe o no es tuya. |
| POST | `/api/v1/direcciones` | Crear. Body: `alias`, `calle`, `numero`, `referencia`, `ciudad`, `codigo_postal`, `es_principal`. |
| PATCH | `/api/v1/direcciones/{direccion_id}` | Actualizar campos parcialmente. |
| PATCH | `/api/v1/direcciones/{direccion_id}/principal` | Marcar como dirección principal. |
| DELETE | `/api/v1/direcciones/{direccion_id}` | Soft delete. |

---

### `/api/v1/pedidos`

Todas requieren **usuario autenticado**. El cliente solo ve sus pedidos; ADMIN/PEDIDOS ven todos.

| Método | Ruta | Auth extra | Descripción |
|--------|------|------------|-------------|
| GET | `/api/v1/pedidos` | — | Lista paginada. Query: `page`, `size`, `estado_codigo`, `usuario_id` (solo staff). |
| POST | `/api/v1/pedidos` | — | Crear pedido. Body: `items[]`, `direccion_entrega_id`, `forma_pago_id`, `observaciones`. Responde 201 con `PedidoRead`. |
| GET | `/api/v1/pedidos/{pedido_id}` | — | Detalle completo con objetos anidados. |
| PATCH | `/api/v1/pedidos/{pedido_id}/estado` | — | Cambiar estado. Body: `{"estado_codigo": "CONFIRMADO", "observacion": "..."}`. Responde 409 si la transición no es válida. |
| GET | `/api/v1/pedidos/{pedido_id}/historial` | — | Historial de cambios de estado con usuario que lo realizó. |
| POST | `/api/v1/pedidos/{pedido_id}/cancelar` | — | Cancela el pedido y devuelve stock. |
| POST | `/api/v1/pedidos/{pedido_id}/avanzar` | **ADMIN** o **PEDIDOS** | Avanza al siguiente estado según cadena. |

**Transiciones de estado válidas:**

| Estado actual | Puede pasar a |
|---------------|---------------|
| `PENDIENTE` | `CONFIRMADO`, `CANCELADO` |
| `CONFIRMADO` | `EN_PREP`, `CANCELADO` |
| `EN_PREP` | `EN_CAMINO` |
| `EN_CAMINO` | `ENTREGADO` |
| `ENTREGADO` | — (final) |
| `CANCELADO` | — (final) |

**`PedidoRead`:**
```json
{
  "id": 1,
  "usuario_id": 2,
  "direccion_entrega": { "id": 1, "calle": "Av. Siempre Viva", "numero": "742", ... },
  "forma_pago": { "id": 1, "codigo": "EFECTIVO", "nombre": "Efectivo", "activa": true },
  "estado": { "id": 1, "codigo": "PENDIENTE", "nombre": "Pendiente", "orden": 1 },
  "total": "1500.00",
  "observaciones": null,
  "fecha_creacion": "2026-05-20T13:00:00",
  "fecha_confirmacion": null,
  "fecha_entrega": null,
  "items": [
    { "producto_id": 3, "producto_nombre": "Café con Leche", "precio_unitario": "350.00", "cantidad": 2, "subtotal": "700.00" }
  ],
  "historial": [
    {
      "estado_anterior": null,
      "estado_nuevo": { "id": 1, "codigo": "PENDIENTE", "nombre": "Pendiente", "orden": 1 },
      "usuario": { "id": 2, "nombre": "Juan" },
      "fecha": "2026-05-20T13:00:00",
      "observacion": null
    }
  ]
}
```

---

### `/api/v1/admin`

Solo rol **ADMIN**.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/admin/usuarios` | Listado paginado. Query: `page`, `size`, `rol` (filtra por código de rol). |
| PATCH | `/api/v1/admin/usuarios/{usuario_id}` | Actualizar datos del usuario. |
| POST | `/api/v1/admin/usuarios/{usuario_id}/roles` | Agregar/quitar roles. Body: `{"agregar": ["STOCK"], "quitar": ["CLIENT"]}`. |
| DELETE | `/api/v1/admin/usuarios/{usuario_id}/roles/{rol_codigo}` | Quitar un rol específico. Responde 204. |
| DELETE | `/api/v1/admin/usuarios/{usuario_id}` | Baja lógica (soft delete). No podés borrar tu propio usuario. |

---

### `/api/v1` — Catálogos públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/formas-pago` | Lista de formas de pago activas: `EFECTIVO`, `TARJETA`, `TRANSFERENCIA`, `MERCADOPAGO`. |
| GET | `/api/v1/estados-pedido` | Lista de estados ordenados por campo `orden`. |

---

## Respuesta paginada

Todos los endpoints con `page`/`size` devuelven:

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

## Códigos HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado |
| 204 | Sin contenido (logout, delete) |
| 400 | Error de negocio (cuenta desactivada, etc.) |
| 401 | No autenticado (falta cookie o token inválido) |
| 403 | Permisos insuficientes |
| 404 | Recurso no encontrado |
| 409 | Conflicto (email duplicado, transición de estado inválida, categoría con productos activos) |
| 422 | Error de validación del body/query (Pydantic) |
| 500 | Error no manejado (detalle en JSON; traceback en consola del servidor) |

---

## Variables de entorno

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Firma del JWT (obligatoria) |
| `JWT_ALGORITHM` | Algoritmo JWT (por defecto `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL del token y max-age de la cookie |
| `BCRYPT_ROUNDS` | Costo del hash de contraseñas |
| `DATABASE_URL` | Conexión PostgreSQL |
| `CORS_ORIGINS` | Orígenes permitidos separados por coma |
| `SEED_ADMIN_EMAIL` | Email del admin inicial (por defecto `admin@foodstore.local`) |
| `SEED_ADMIN_PASSWORD` | Contraseña del admin inicial (por defecto `Admin1234!`) |

---

*Rama activa: `rama-adrian-fredes` en `adrianfredes10/backend-foodstore`. Para cambios de rutas actualizá este archivo o usá `/docs` como referencia en tiempo de ejecución.*
