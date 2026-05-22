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

Las tablas y los datos obligatorios (roles, estados, formas de pago, usuario admin) se crean automáticamente al iniciar.

### 4. (Opcional) Cargar datos de prueba

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
│   └── security.py       # hash_password, verify_password, JWT
├── deps/
│   └── auth_deps.py      # get_current_user, require_roles
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

- Login con JSON `{"email": "...", "password": "..."}` → cookie HttpOnly `access_token` (JWT, 30 min)
- El front debe enviar cookies: `withCredentials: true` en Axios o `credentials: "include"` en fetch
- Roles: `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT`

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
| `/api/v1/formas-pago` | Catálogo público de formas de pago |
| `/api/v1/estados-pedido` | Catálogo público de estados |

## Usuario admin por defecto

| Campo | Valor |
|---|---|
| Email | `admin@foodstore.local` |
| Contraseña | `Admin1234!` |

Configurable con `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD` en `.env`.
