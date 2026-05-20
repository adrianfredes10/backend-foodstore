# Documentación de rutas — Food Store API

Base URL típica en desarrollo: `http://localhost:8000` (ajustá el puerto si lo cambiás).

Documentación interactiva: **`GET /docs`** (Swagger) y **`GET /redoc`**.

---

## Autenticación (JWT)

El backend **usa JWT** (librería **PyJWT**, algoritmo por defecto **HS256**).

- **Login** (`POST /api/v1/auth/login`) devuelve JSON `{"ok": true}` y setea una **cookie HttpOnly** llamada **`access_token`** con el token JWT dentro.
- **Vencimiento:** configurado en `ACCESS_TOKEN_EXPIRE_MINUTES` (por defecto **30** minutos en `app/core/config.py`).
- **Clave secreta:** variable de entorno **`SECRET_KEY`** (obligatoria, mínimo 16 caracteres).
- Las rutas protegidas leen el JWT desde esa **cookie** (`COOKIE_NAME = "access_token"` en `app/deps/auth_deps.py`), no desde el header `Authorization: Bearer` (a menos que el front envíe el token por otro mecanismo; hoy el servidor espera cookie).

**Para probar desde el navegador / front en otro origen:** el CORS permite orígenes definidos en `CORS_ORIGINS` y `allow_credentials=True`; el cliente debe enviar cookies (`credentials: "include"` en fetch, o equivalente).

**Rutas públicas (sin cookie):** registro, login, listados de lectura que no inyectan `get_current_user` / `require_roles` (ver tabla abajo).

---

## Códigos de rol (referencia)

Definidos en `app/constants/codigos.py` (strings en mayúsculas):

| Código   | Uso típico                          |
|----------|-------------------------------------|
| `ADMIN`  | ABM categorías/productos/ingredientes, panel admin, avanzar pedido |
| `STOCK`  | Stock y disponibilidad de productos |
| `PEDIDOS`| Avanzar estado de pedidos (junto con ADMIN) |
| `CLIENT` | Cliente registrado (registro asigna este rol) |

---

## Resumen por prefijo

| Prefijo | Rol / auth |
|---------|------------|
| `/api/v1/auth` | Público salvo `/me` |
| `/api/v1/categorias` | GET público; POST/PUT/DELETE requieren **ADMIN** |
| `/api/v1/ingredientes` | GET público; POST/PUT/DELETE requieren **ADMIN** |
| `/api/v1/productos` | GET público; escritura según ruta (ver tabla) |
| `/api/v1/direcciones` | Todas requieren usuario logueado |
| `/api/v1/pedidos` | Logueado; avanzar estado: **ADMIN** o **PEDIDOS** |
| `/api/v1/admin` | Solo **ADMIN** |

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
| POST | `/api/v1/auth/register` | No | Alta de usuario (body JSON `RegistroRequest`: email, password). |
| POST | `/api/v1/auth/login` | No | Login con **formulario** estilo OAuth2 (`username` = email, `password`). Responde `{"ok": true}` y cookie `access_token` (JWT). |
| GET | `/api/v1/auth/me` | Sí (cookie JWT) | Perfil del usuario actual (`UsuarioPublic`). |

---

### `/api/v1/categorias`

| Método | Ruta | Auth | Query / notas |
|--------|------|------|-----------------|
| GET | `/api/v1/categorias` | No | `skip`, `limit`, `parent_id` (opcional), `recursivo` (bool, árbol/CTE si aplica). |
| GET | `/api/v1/categorias/{id}` | No | Una categoría por id. |
| POST | `/api/v1/categorias` | **ADMIN** | Crear. |
| PUT | `/api/v1/categorias/{id}` | **ADMIN** | Actualizar. |
| DELETE | `/api/v1/categorias/{id}` | **ADMIN** | Borrado lógico según servicio. |

---

### `/api/v1/ingredientes`

| Método | Ruta | Auth |
|--------|------|------|
| GET | `/api/v1/ingredientes` | No (`skip`, `limit`) |
| GET | `/api/v1/ingredientes/{id}` | No |
| POST | `/api/v1/ingredientes` | **ADMIN** |
| PUT | `/api/v1/ingredientes/{id}` | **ADMIN** |
| DELETE | `/api/v1/ingredientes/{id}` | **ADMIN** |

---

### `/api/v1/productos`

| Método | Ruta | Auth | Notas |
|--------|------|------|--------|
| GET | `/api/v1/productos` | No | `skip`, `limit`, `categoria_id`, `disponible`, `q` (búsqueda). |
| GET | `/api/v1/productos/{id}` | No | Detalle. |
| PATCH | `/api/v1/productos/{id}/stock` | **ADMIN** o **STOCK** | Body: cantidad de stock. |
| PATCH | `/api/v1/productos/{id}/disponibilidad` | **ADMIN** o **STOCK** | Body: disponible si/no. |
| POST | `/api/v1/productos` | **ADMIN** | Crear. |
| PUT | `/api/v1/productos/{id}` | **ADMIN** | Actualizar. |
| DELETE | `/api/v1/productos/{id}` | **ADMIN** | Borrado lógico según servicio. |

---

### `/api/v1/direcciones`

Todas requieren **usuario autenticado** (cookie JWT).

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/direcciones` | Listado del usuario. |
| POST | `/api/v1/direcciones` | Crear dirección. |
| PATCH | `/api/v1/direcciones/{direccion_id}` | Actualizar. |
| PATCH | `/api/v1/direcciones/{direccion_id}/principal` | Marcar como principal. |
| DELETE | `/api/v1/direcciones/{direccion_id}` | Soft delete. |

---

### `/api/v1/pedidos`

Requieren **usuario autenticado**. Listado y detalle aplican reglas de negocio: cliente ve lo suyo; staff ve más según roles.

| Método | Ruta | Auth extra | Descripción |
|--------|------|------------|-------------|
| GET | `/api/v1/pedidos` | — | Lista paginada (`skip`, `limit`). |
| POST | `/api/v1/pedidos` | — | Crear pedido. |
| GET | `/api/v1/pedidos/{pedido_id}` | — | Detalle (historial/snapshot según implementación). |
| POST | `/api/v1/pedidos/{pedido_id}/cancelar` | — | Cancelar (reglas en servicio). |
| POST | `/api/v1/pedidos/{pedido_id}/avanzar` | **ADMIN** o **PEDIDOS** | Avanzar estado del pedido. |

---

### `/api/v1/admin`

Solo rol **ADMIN**.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/admin/usuarios` | Listado paginado (`skip`, `limit`, `rol` opcional para filtrar por código de rol). |
| PATCH | `/api/v1/admin/usuarios/{usuario_id}` | Actualizar usuario (`disabled`, opcional `roles_codigos` reemplaza todos los roles). |
| POST | `/api/v1/admin/usuarios/{usuario_id}/roles` | **Agregar y/o quitar** roles sin reemplazar todo: body JSON con `agregar` y/o `quitar` (listas de códigos de rol). |
| DELETE | `/api/v1/admin/usuarios/{usuario_id}` | Baja lógica; no podés borrar tu propio usuario. |

---

## Códigos HTTP habituales

- **200** OK, **201** Created, **204** No Content  
- **400** Bad Request (validación / regla de negocio)  
- **401** No autenticado (falta cookie o token inválido)  
- **403** Permisos insuficientes  
- **404** Recurso no encontrado  
- **422** Error de validación del body/query (Pydantic)  
- **500** Error no manejado (detalle acotado en JSON; traceback en consola del servidor)

---

## Variables de entorno relevantes

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Firma del JWT |
| `JWT_ALGORITHM` | Por defecto `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL del token (y max-age de la cookie en login) |
| `BCRYPT_ROUNDS` | Hash de contraseñas |
| `DATABASE_URL` | Conexión PostgreSQL |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma |

---

*Generado como referencia del proyecto `backend-foodstore`. Si cambiás routers, actualizá este archivo o confiá en `/docs` como fuente en tiempo de ejecución.*
