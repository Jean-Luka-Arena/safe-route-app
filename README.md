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

Safe Route modela la ciudad como un **grafo ponderado**: cada intersección es
un vértice, cada calle una arista con dos atributos, distancia y seguridad.
Sobre ese grafo corre un algoritmo de caminos mínimos (Dijkstra) parametrizado
por una **función de costo**, lo que permite calcular tres tipos de ruta sin
duplicar el algoritmo:

- **Más corta** — minimiza la distancia total.
- **Más segura** — minimiza `distancia × riesgo`, con `riesgo = 10 - seguridad`.
- **Balanceada** — combina ambos criterios con pesos configurables (`alpha`,
  `beta`) que el usuario puede ajustar.

Además, los usuarios pueden **reportar incidentes** (robos, zonas oscuras,
calles bloqueadas, accidentes) sobre una calle puntual. Esos reportes bajan
dinámicamente la seguridad *evaluada* de esa calle en los próximos cálculos
de ruta, sin alterar el dato de seguridad "de base" cargado originalmente.

## Arquitectura

```
Cliente (navegador / Swagger UI)
        │
        ▼
   FastAPI (rutas.py, incidentes.py)
        │
        ▼
   Services (motor_rutas.py)
        │
        ├── Algorithms (dijkstra genérico + funciones de costo)
        │
        └── Repositories (arma el grafo leyendo de la base)
                │
                ▼
          PostgreSQL (Ubicacion, Conexion, Incidente)
```

La lógica de negocio (algoritmos, cálculo de rutas) está desacoplada de la
base de datos y de la capa HTTP: el service `calcular_ruta` no sabe que
existe FastAPI, y el algoritmo `dijkstra` no sabe que existe Postgres.

### Estructura de carpetas

```
safe-route-app/
├── docker-compose.yml          # levanta PostgreSQL
├── data/
│   └── seed.json                # datos de ejemplo (ubicaciones y calles)
└── backend/
    ├── requirements.txt
    ├── pytest.ini
    └── app/
        ├── main.py               # arma la app de FastAPI
        ├── rutas.py              # GET /route
        ├── incidentes.py         # POST /incidents
        ├── schemas.py            # validación de requests (Pydantic)
        ├── tda_grafo/            # Grafo genérico + GrafoCiudad + AtributosCalle
        ├── algorithms/           # dijkstra genérico + funciones de costo
        ├── services/             # motor_rutas: orquesta todo lo anterior
        ├── repositories/         # arma GrafoCiudad leyendo de la base
        └── db/                   # conexión, modelos SQLAlchemy, seed
```

## Tecnologías utilizadas

| Capa               | Tecnología                     |
|---------------------|--------------------------------|
| Lenguaje            | Python 3.12                    |
| API                 | FastAPI + Uvicorn               |
| Base de datos       | PostgreSQL 16                  |
| ORM                 | SQLAlchemy 2.x                 |
| Validación          | Pydantic                       |
| Tests               | pytest                         |
| Infraestructura     | Docker / docker-compose         |

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
cp ../.env.example ../.env   # variables de conexión a la base
```

### 3. Crear las tablas y cargar datos de ejemplo

```bash
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

Documentación interactiva disponible en `http://127.0.0.1:8000/docs`.

## Uso de la API

**Calcular una ruta:**
```
GET /route?origin=1&destination=4&criteria=segura
```
`criteria` puede ser `corta`, `segura` o `balanceada` (esta última requiere
además los parámetros `alpha` y `beta`).

Respuesta:
```json
{
  "ruta": [1, 2, 4],
  "distancia_total": 1200,
  "seguridad_promedio": 8.5,
  "costo_total": 1700
}
```

**Reportar un incidente:**
```
POST /incidents
Content-Type: application/json

{
  "conexion_id": 5,
  "tipo": "robo",
  "gravedad": 8
}
```
`tipo` acepta: `robo`, `zona_oscura`, `calle_bloqueada`, `accidente`.

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
  incidentes. Esto preserva el dato original de seguridad de base.

### Limitaciones conocidas (mejoras futuras)

- Los incidentes se acumulan **sin decaimiento temporal**: un incidente de
  hace un año pesa igual que uno de ayer. Una mejora futura sería ponderar
  por antigüedad.
- La seguridad efectiva no varía según la hora del día, aunque el modelo ya
  guarda fecha y hora completas de cada incidente (`DateTime`). Se podría
  incorporar una franja horaria al cálculo más adelante.
- `A*` no está implementado (Dijkstra cubre el requisito obligatorio de la
  consigna).

## Estado del proyecto

- [x] Entrega 1 — Núcleo algorítmico (grafo, Dijkstra, funciones de costo)
- [x] Entrega 2 — Backend (API con FastAPI)
- [x] Entrega 3 — Base de datos y seguridad dinámica
- [ ] Entrega 4 — Frontend
- [ ] Entrega 5 — Docker completo, CI/CD, deploy, demo