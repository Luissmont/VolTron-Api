# VolTron API

VolTron es una plataforma para diseñar proyectos de robótica y electrónica de forma inteligente. Este repositorio contiene el backend: una API REST construida con FastAPI que actúa como capa intermediaria entre la interfaz de usuario y la base de datos, exponiendo toda la lógica del sistema a través de endpoints bien definidos.

La API es completamente independiente del frontend y de la base de datos. Puede ser consumida por cualquier cliente HTTP, ya sea una aplicación web, móvil o herramientas como Postman o Swagger.


## Qué hace esta API

El sistema permite que un usuario (registrado o anónimo) explore un catálogo de componentes electrónicos, cree un proyecto robótico, le agregue piezas de ese catálogo y finalmente consulte una validación automática que indica si el proyecto es eléctricamente viable o si existe riesgo de sobrecarga.

Adicionalmente, cada componente del catálogo muestra su precio tanto en dólares americanos (tal como está almacenado en la base de datos) como en Pesos Mexicanos, calculado en tiempo real consultando una API europea de tipos de cambio llamada Frankfurter.


## Decisiones técnicas importantes

**Por qué FastAPI:** Elegimos FastAPI porque es asíncrono por naturaleza, lo que le permite manejar múltiples peticiones simultáneas sin bloquearse. Esto es importante cuando la API necesita consultar la base de datos y al mismo tiempo esperar la respuesta de un servicio externo.

**Por qué usamos SQL puro en lugar del ORM:** SQLAlchemy tiene dos modos de uso. El primero es el ORM clásico (donde defines clases Python que representan tablas). El segundo es usar SQLAlchemy solo como motor de conexión asíncrona y escribir el SQL directamente mediante `text()`. Elegimos este segundo enfoque porque nuestras consultas más importantes (como la validación de proyectos) se apoyan en una vista compleja de PostgreSQL. Intentar replicar esa lógica con el ORM sería más complicado y menos eficiente que simplemente invocar `SELECT * FROM vw_project_validation`. Los datos llegan limpios desde la base de datos y Pydantic los valida antes de responder al cliente.

**Por qué Pydantic en todos los endpoints:** Cada entrada y cada salida de la API pasa por un esquema Pydantic. Esto garantiza que si alguien envía un JSON mal formado, la API responde con un error 422 descriptivo antes de tocar la base de datos. No hay validación hecha a mano.

**Seguridad por diseño:** Las contraseñas nunca se guardan en texto plano. En el momento del registro se transforman con el algoritmo bcrypt, que es un hash unidireccional imposible de revertir. El sistema de sesiones funciona mediante tokens JWT de tiempo limitado. Además, todas las consultas a la base de datos utilizan parámetros vinculados (`WHERE id = :id`), lo que elimina completamente la posibilidad de inyección SQL.


## Requisitos para ejecutarlo

Necesitas tener instalado Python 3.11 o superior y Docker Desktop. La base de datos corre en un contenedor Docker que se levanta desde el repositorio hermano `VolTronDatabase`.


## Instrucciones de instalación

Primero, levanta la base de datos desde el directorio de `VolTronDatabase`:

```bash
docker compose up -d --build
```

Puedes verificar que los contenedores están activos con `docker ps`. Deberías ver `voltron_postgres` escuchando en el puerto 5433.

Luego, crea el entorno virtual e instala las dependencias de Python:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Antes de arrancar el servidor, necesitas crear un archivo `.env` en la raíz del proyecto con las variables de configuración. Este archivo no está incluido en el repositorio porque contiene información sensible.

DB_USER=
DB_PASSWORD=
DB_NAME=
DB_HOST=
DB_PORT=

SECRET_KEY=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=



Finalmente, arranca el servidor:

python -m uvicorn app.main:app --reload


El servidor queda disponible en `http://localhost:8000`. La documentación interactiva generada automáticamente por FastAPI está en `http://localhost:8000/docs`, donde puedes probar todos los endpoints directamente desde el navegador.


## Endpoints disponibles

La API expone los siguientes grupos de rutas:

**Verificación del sistema**
- `GET /health` — Confirma que la API está en pie y que la conexión con la base de datos es exitosa.

**Autenticación**
- `POST /api/auth/register` — Registra un nuevo usuario. Recibe email y contraseña; devuelve el perfil creado.
- `POST /api/auth/login` — Autentica un usuario y devuelve un token JWT que debe usarse en las siguientes peticiones que lo requieran.

**Catálogo de componentes**
- `GET /api/components/` — Devuelve todos los componentes activos del catálogo. Cada uno incluye especificaciones técnicas, precio en dólares y precio en pesos mexicanos calculado al momento.

**Proyectos**
- `POST /api/projects/` — Crea un proyecto nuevo. Si se envía el token JWT el proyecto queda vinculado al usuario; si no, se crea de forma anónima.
- `POST /api/projects/{project_id}/components` — Agrega un componente del catálogo al proyecto indicado.
- `GET /api/projects/{project_id}/validation` — Consulta la validación eléctrica del proyecto. Retorna si el consumo de corriente es seguro, si el voltaje es compatible y si hay riesgo de sobrecarga.


## Cómo probar el flujo completo

Este es el flujo de uso esperado desde cero:

```bash
# Paso 1: Registrar un usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@demo.com", "password": "password123"}'

# Paso 2: Iniciar sesión y guardar el token
curl -X POST http://localhost:8000/api/auth/login \
  -F "username=usuario@demo.com" \
  -F "password=password123"

# Paso 3: Ver el catálogo de componentes con precios en MXN
curl http://localhost:8000/api/components/

# Paso 4: Crear un proyecto autenticado (reemplaza TOKEN con el valor del paso 2)
curl -X POST http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Robot seguidor de línea"}'

# Paso 5: Agregar un componente al proyecto (reemplaza los IDs correspondientes)
curl -X POST http://localhost:8000/api/projects/PROJECT_ID/components \
  -H "Content-Type: application/json" \
  -d '{"component_id": "ID_DEL_COMPONENTE", "quantity": 1}'

# Paso 6: Validar si el proyecto es eléctricamente viable
curl http://localhost:8000/api/projects/PROJECT_ID/validation
```


## Tecnologías utilizadas

El proyecto usa las siguientes dependencias principales:

- **FastAPI** como framework web asíncrono.
- **SQLAlchemy** como motor de conexión asíncrona a la base de datos (usamos SQL puro con `text()`, no el ORM).
- **asyncpg** como driver nativo de PostgreSQL para Python asíncrono.
- **Pydantic v2** para validación de todos los datos de entrada y salida.
- **passlib con bcrypt** para el hashing seguro de contraseñas.
- **python-jose** para la generación y verificación de tokens JWT.
- **httpx** como cliente HTTP asíncrono para consultar la API de divisas Frankfurter.
- **pydantic-settings** para leer las variables de entorno de forma tipada y segura.
- **PostgreSQL 15** corriendo en Docker como base de datos relacional.


