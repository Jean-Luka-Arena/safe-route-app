# Safe Route

Sistema de planificación de rutas urbanas que, además de la distancia, tiene en
cuenta un **nivel de seguridad** por calle a la hora de calcular el mejor
camino entre dos puntos de una ciudad.

## El problema

Las apps de navegación tradicionales optimizan casi exclusivamente por
distancia o tiempo. Pero en muchos contextos, el camino más corto no es el
que uno elegiría a pie o de noche: hay calles más iluminadas, más
transitadas, o con menos incidentes reportados que otras. Safe Route busca
resolver eso: dejar que el usuario elija **qué le importa más** a la hora de
moverse por la ciudad.

## La solución

Safe Route modela la ciudad como un **grafo ponderado**, construido a partir
de calles reales de OpenStreetMap (hoy, la zona de Vicente López / Olivos):
cada intersección es un vértice, cada calle una arista con dos atributos,
distancia y seguridad. Sobre ese grafo corre un algoritmo de caminos mínimos
(Dijkstra) parametrizado por una **función de costo**, lo que permite
calcular tres tipos de ruta sin duplicar el algoritmo:

- **Más corta** — minimiza la distancia total.
- **Más segura** — minimiza `distancia × riesgo`, con `riesgo = 10 - seguridad`.
- **Balanceada** — combina ambos criterios con pesos configurables (`alpha`,
  `beta`, entre 0 y 1) que el usuario puede ajustar.

Los usuarios registrados pueden **reportar incidentes** (robos, zonas
oscuras, calles bloqueadas, accidentes) sobre una calle puntual. Esos
reportes bajan dinámicamente la seguridad *evaluada* de esa calle en los
próximos cálculos de ruta, sin alterar el dato de seguridad "de base"
cargado originalmente. La gravedad de cada reporte la asigna el sistema
según el tipo (no el usuario que reporta, para evitar que alguien la
exagere a propósito), y cada usuario puede borrar sus propios reportes si se
equivocó.

## Arquitectura

```
Navegador (frontend/ con Leaflet)
        │
        ▼
   FastAPI (rutas.py, incidentes.py, auth.py, ubicaciones.py, conexiones.py)
        │
        ▼
   Services (motor_rutas.py, incidentes_service.py, auth_service.py)
        │
        ├── Algorithms (dijkstra genérico + funciones de costo)
        │
        └── Repositories (arma el grafo leyendo de la base)
                │
                ▼
   PostgreSQL (Ubicacion, Conexion, Incidente, Usuario)
```

La lógica de negocio (algoritmos, cálculo de rutas, reglas de incidentes)
está desacoplada de la base de datos y de la capa HTTP: los services no
saben que existe FastAPI, y el algoritmo `dijkstra` no sabe que existe
Postgres. Cada router (`rutas.py`, `incidentes.py`, `auth.py`) es una capa
HTTP finita que solo traduce pedidos hacia/desde su service correspondiente.

### Estructura de carpetas

```
safe-route-app/
├── docker-compose.yml           # levanta PostgreSQL
├── .env.example                 # variables de entorno (DB + JWT)
├── data/
│   └── seed.json                 # ubicaciones y calles (generado desde OSM)
├── scripts/
│   └── generar_seed_desde_osm.py # trae calles reales vía Overpass API
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── config.js
└── backend/
    ├── requirements.txt
    ├── pytest.ini
    └── app/
        ├── main.py               # arma la app de FastAPI
        ├── rutas.py              # GET /route
        ├── incidentes.py         # POST/GET/DELETE /incidents
        ├── auth.py               # POST /register, POST /login
        ├── ubicaciones.py        # GET /locations
        ├── conexiones.py         # GET /connections
        ├── dependencias.py       # autenticación (JWT) para endpoints protegidos
        ├── schemas.py            # validación de requests (Pydantic)
        ├── tda_grafo/            # Grafo genérico + GrafoCiudad + AtributosCalle
        ├── algorithms/           # dijkstra genérico + funciones de costo
        ├── services/             # motor_rutas, incidentes_service, auth_service
        ├── repositories/         # arma GrafoCiudad leyendo de la base
        └── db/                   # conexión, modelos SQLAlchemy, seed
```

## Tecnologías utilizadas

| Capa               | Tecnología                              |
|---------------------|------------------------------------------|
| Lenguaje            | Python 3.12                             |
| API                 | FastAPI + Uvicorn                        |
| Base de datos       | PostgreSQL 16                           |
| ORM                 | SQLAlchemy 2.x                          |
| Validación          | Pydantic                                |
| Autenticación       | JWT (PyJWT) + bcrypt                    |
| Tests               | pytest                                  |
| Frontend            | HTML/CSS/JS plano + Leaflet             |
| Geocodificación     | Nominatim (OpenStreetMap)                |
| Ruteo visual        | OSRM (dibuja la ruta siguiendo calles)   |
| Datos de la ciudad  | Overpass API (OpenStreetMap)             |
| Infraestructura     | Docker / docker-compose                  |

## Cómo ejecutar el proyecto

### 1. Levantar la base de datos

```bash
docker compose up -d
```

### 2. Preparar el entorno de Python

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
```

Editá `.env` y poné una `SECRET_KEY` propia (por ejemplo, generada con
`python3 -c "import secrets; print(secrets.token_hex(32))"`).

### 3. Generar los datos de la ciudad y cargarlos

```bash
cd ..
python scripts/generar_seed_desde_osm.py
cd backend
python -m app.db.crear_tablas
python -m app.db.seed
```

### 4. Correr los tests

```bash
pytest -v
```

### 5. Levantar la API

```bash
uvicorn app.main:app --reload
```

Documentación interactiva en `http://127.0.0.1:8000/docs`.

### 6. Levantar el frontend

En otra terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Y abrir `http://localhost:5500/index.html`.

## Uso de la API

**Registrarse e iniciar sesión:**
```
POST /register   { "email": "vos@ejemplo.com", "password": "12345678" }
POST /login       { "email": "vos@ejemplo.com", "password": "12345678" }
```
`/login` devuelve un `access_token` (JWT) que hay que mandar como header
`Authorization: Bearer <token>` en los endpoints protegidos.

**Calcular una ruta** (no requiere login):
```
GET /route?origin=1&destination=4&criteria=segura
```
`criteria` puede ser `corta`, `segura` o `balanceada` (esta última requiere
además `alpha` y `beta`, entre 0 y 1).

Respuesta:
```json
{
  "ruta": [1, 2, 4],
  "distancia_total": 1200,
  "seguridad_promedio": 8.5,
  "costo_total": 1700
}
```

**Reportar un incidente** (requiere login):
```
POST /incidents
Authorization: Bearer <token>
Content-Type: application/json

{ "conexion_id": 5, "tipo": "robo" }
```
`tipo` acepta: `robo`, `zona_oscura`, `calle_bloqueada`, `accidente`. La
gravedad la asigna el servidor según el tipo, no el usuario.

**Ver y borrar tus propios reportes** (requiere login):
```
GET /incidents/mine
DELETE /incidents/{id}
```
Borrar un incidente que no es tuyo devuelve `403`.

## Decisiones de diseño

- **Composición sobre herencia**: `GrafoCiudad` compone un `Grafo` genérico
  en vez de heredar de él, para no acoplar la lógica de dominio (calles,
  ubicaciones) al TDA genérico.
- **Dijkstra parametrizado por función de costo**: un único algoritmo sirve
  para las tres rutas (corta/segura/balanceada), sin duplicar código (DRY).
  Complejidad temporal `O((V + E) log V)` con heap binario; espacial
  `O(V + E)`.
- **Seguridad como evaluación derivada, no como dato mutado**: los incidentes
  no modifican `nivel_seguridad` en la tabla `Conexion`; se recalcula una
  "seguridad efectiva" en cada consulta, restando la gravedad acumulada de
  incidentes.
- **Gravedad asignada por el sistema, no por quien reporta**: cada tipo de
  incidente tiene una gravedad fija predefinida, para que nadie pueda
  exagerar a propósito el impacto de un reporte falso.
- **Autenticación liviana con JWT**: en vez de sesiones con estado en el
  servidor, cada usuario recibe un token firmado que probamos localmente en
  cada pedido protegido, sin necesidad de una tabla de sesiones.
- **Arquitectura en capas simétrica**: cada recurso (rutas, incidentes, auth)
  tiene su propio router (HTTP) y su propio service (lógica de negocio +
  persistencia), replicando siempre el mismo patrón para que el código sea
  predecible.
- **Datos de la ciudad generados, no hardcodeados**: `scripts/generar_seed_desde_osm.py`
  arma `data/seed.json` a partir de datos reales de OpenStreetMap (calles,
  distancias reales por haversine, e iluminación como heurística inicial de
  seguridad), en vez de mantener datos de prueba a mano.

### Limitaciones conocidas (mejoras futuras)

- Los incidentes se acumulan **sin decaimiento temporal**: un incidente de
  hace un año pesa igual que uno de ayer.
- La seguridad efectiva no varía según la hora del día, aunque el modelo ya
  guarda fecha y hora completas de cada incidente.
- `A*` no está implementado (Dijkstra cubre el requisito obligatorio de la
  consigna).
- La autenticación es propia (JWT + bcrypt), sin recuperación de contraseña
  ni verificación de email — suficiente para el alcance actual del proyecto,
  no para producción real.
- El frontend depende de tres servicios públicos gratuitos (Nominatim, OSRM,
  Overpass), cada uno con límites de uso razonables para una demo pero no
  pensados para tráfico alto.

## Estado del proyecto

- [x] Entrega 1 — Núcleo algorítmico (grafo, Dijkstra, funciones de costo)
- [x] Entrega 2 — Backend (API con FastAPI)
- [x] Entrega 3 — Base de datos y seguridad dinámica
- [x] Entrega 4 — Frontend (mapa, búsqueda de direcciones, usuarios, reportes)
- [ ] Entrega 5 — Docker completo, CI/CD, deploy, demo