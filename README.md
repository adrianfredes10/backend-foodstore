# Backend — Food Store API

API REST para el sistema de pedidos FoodStore. Construida con FastAPI, SQLModel y PostgreSQL.

## Stack

| Tecnología | Uso |
|---|---|
| FastAPI | Framework web |
| SQLModel | ORM con tipado (Pydantic + SQLAlchemy) |
| PostgreSQL | Base de datos |
| Uvicorn | Servidor ASGI |
| python-jose | JWT (HS256) |
| passlib + bcrypt | Hash de contraseñas (cost factor 12) |

## Cómo correr el proyecto

### 1. Levantar PostgreSQL con Docker

```bash
docker compose up -d
```

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5434` |
| Usuario | `postgres` |
| Contraseña | `1234postgres` |
| Base de datos | `parcial_prog4` |

### 2. Configurar el entorno

Crear `.env` a partir de `.env.example`:

```env
DATABASE_URL=postgresql://postgres:1234postgres@localhost:5434/parcial_prog4
SECRET_KEY=tu_clave_secreta_minimo_16_chars
```

### 3. Instalar dependencias y correr

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app
```

La API queda en `http://localhost:8000`  
Documentación interactiva en `http://localhost:8000/docs`

En base **nueva** las tablas se crean solas (`create_all`) y el seed obligatorio
carga roles, estados, formas de pago, unidades de medida y usuario admin.

### 4. Migraciones (solo en bases existentes de parciales previos)

Si la base ya existía, correr en orden los scripts de `migrations/` que falten:

```bash
# ejemplo con psql
psql "$DATABASE_URL" -f migrations/004_fsm_5_estados.sql
psql "$DATABASE_URL" -f migrations/005_pedido_montos_v7.sql
psql "$DATABASE_URL" -f migrations/006_unidad_medida.sql
psql "$DATABASE_URL" -f migrations/007_categoria_imagen.sql
psql "$DATABASE_URL" -f migrations/008_usuariorol_expires.sql
psql "$DATABASE_URL" -f migrations/009_refresh_token.sql
psql "$DATABASE_URL" -f migrations/010_producto_imagen_public_id.sql
psql "$DATABASE_URL" -f migrations/011_producto_imagenes_array.sql
```

Todas son idempotentes (`IF NOT EXISTS`), se pueden re-ejecutar sin romper.

### 5. (Opcional) Cargar datos de prueba

```bash
python seed.py
```

## Estructura

```
app/
├── main.py               # app FastAPI, CORS, routers, startup
├── database.py           # engine y create_db_and_tables
├── uow.py                # Unit of Work (sesión, commit/rollback)
├── seed_obligatorio.py   # seed que corre en startup (idempotente)
├── constants/            # códigos de rol y estado
├── core/
│   ├── config.py         # Settings con pydantic-settings
│   ├── security.py       # hash_password, JWT, refresh token
│   ├── auth_deps.py      # get_current_user, require_roles (cookie JWT)
│   ├── exceptions.py     # handlers RFC 7807 (problem+json)
│   ├── rate_limit.py     # middleware token bucket (login/register)
│   └── ws_manager.py     # ConnectionManager WebSocket (rooms)
├── models/               # tablas SQLModel
├── schemas/              # DTOs Pydantic (Create, Read, Update)
├── repositories/         # acceso a base de datos
├── services/             # lógica de negocio
└── routers/              # endpoints HTTP
```

## Arquitectura

Patrón **Router → Service → Repository → UnitOfWork**:

- **Router**: recibe el request, valida con `Annotated` + `Query`/`Path`, delega al service
- **Service**: orquesta lógica de negocio, lanza `HTTPException` si algo falla. Nunca hace `session.commit()` directamente
- **Repository**: ejecuta queries contra la BD. Hereda de `BaseRepository[T]`
- **UnitOfWork**: controla la sesión — `commit` automático si todo salió bien, `rollback` si algo falló

Patrones adicionales:
- **Snapshot Pattern**: `DetallePedido` guarda `producto_nombre` y `precio_unitario` al momento de crear el pedido
- **Audit Trail**: `HistorialEstadoPedido` es append-only (solo INSERTs, jamás UPDATE/DELETE)
- **Soft Delete**: `deleted_at` en todas las entidades de negocio

## Autenticación

- Login con JSON `{"email": "...", "password": "..."}` → cookies HttpOnly `access_token` (JWT, 30 min) + `refresh_token` (7 días, path `/api/v1/auth`)
- `POST /api/v1/auth/refresh`: rota el refresh (revoca el viejo) y renueva el access
- `POST /api/v1/auth/logout`: revoca el refresh y borra ambas cookies (requiere auth)
- Contraseñas hasheadas con **bcrypt cost factor 12** (`BCRYPT_ROUNDS` en `.env`, default 12)
- El front debe enviar cookies: `withCredentials: true` en Axios o `credentials: "include"` en fetch
- Roles: `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT`

## Middlewares y errores

- **Rate limit** en `login`/`register`: 5 intentos / 15 min por IP → `429` + header `Retry-After` (`RATE_LIMIT_AUTH_MAX`, `RATE_LIMIT_AUTH_WINDOW_MINUTES`)
- **Errores RFC 7807** (`application/problem+json`): `type`, `title`, `status`, `detail`, `instance`. Se conserva `detail` para compatibilidad
- **CORS** con credenciales habilitadas (`CORS_ORIGINS`)

## WebSocket

- `WS /ws/pedidos` — feed de staff (ADMIN/PEDIDOS) con cambios de estado de pedidos en tiempo real
- Auth por cookie `access_token` (se envía sola en el handshake)
- Close codes: `4001` token expirado (el front refresca y reconecta), `1008` sin sesión / token inválido / rol no permitido
- Eventos (payload plano): `estado_cambiado`, `pedido_cancelado`, `pago_confirmado`
- El broadcast se emite **post-commit, fuera del UoW** (RN-06)

## Imágenes (Cloudinary)

- `POST /api/v1/uploads/producto/{id}/imagen` (ADMIN, `multipart/form-data`, campo `file`): sube a Cloudinary, guarda `imagen_url` + `public_id` en el producto y borra la anterior si había
- `DELETE /api/v1/uploads/producto/{id}/imagen` (ADMIN): borra de Cloudinary y limpia `imagen_url`
- Tipos: `jpeg`, `png`, `webp`, `gif`. Máx **5MB**. Folder `foodstore/productos`
- Las llamadas a Cloudinary corren **fuera del UoW** (I/O de red, no parte de la transacción)
- Credenciales por `.env`: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (el secret nunca se commitea)

## Endpoints principales

Todos bajo `/api/v1/`. Ver documentación completa en `/docs` o en `docs/API_RUTAS.md`.

| Prefijo | Descripción |
|---|---|
| `/api/v1/auth` | Registro, login, logout, perfil |
| `/api/v1/categorias` | CRUD categorías (jerarquía, soft delete) |
| `/api/v1/ingredientes` | CRUD ingredientes |
| `/api/v1/productos` | CRUD productos + stock + disponibilidad |
| `/api/v1/direcciones` | Direcciones de entrega del usuario |
| `/api/v1/pedidos` | Pedidos con máquina de estados |
| `/api/v1/admin` | Gestión de usuarios y roles (solo ADMIN) |
| `/api/v1/uploads` | Imágenes de productos en Cloudinary (solo ADMIN) |
| `/api/v1/formas-pago` | Catálogo público de formas de pago |
| `/api/v1/estados-pedido` | Catálogo público de estados (con `es_terminal`) |
| `/api/v1/unidades-medida` | Catálogo público de unidades de medida |
| `/ws/pedidos` | WebSocket feed de staff (tiempo real) |

## Usuario admin por defecto

| Campo | Valor |
|---|---|
| Email | `admin@foodstore.local` |
| Contraseña | `Admin1234!` |

Configurable con `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD` en `.env`.
