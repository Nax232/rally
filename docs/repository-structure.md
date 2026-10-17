# SIPRE — Estructura propuesta del repositorio

Fecha: 2026-10-16. Sólo `docs/` se crea en F8. El árbol siguiente es diseño para implementación autorizada, no inventario de código existente.

## Árbol objetivo

```text
Rally/
├── SIPRE_*.md / SIPRE_*.json / SIPRE_FASE7_SHA256.txt  # fuentes originales preservadas
├── PROMPT_CODEX_SIPRE_FASE7.md / README_ENTREGA_FASE7.md
├── AGENTS.md                         # instrucciones futuras aprobadas, si el equipo lo solicita
├── README.md                         # instalación y demostración
├── pyproject.toml                    # paquete backend y dependencias declaradas
├── requirements.lock / requirements-dev.lock  # pins y hashes generados en H1
├── compose.yaml / .env.example / .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py                   # composición FastAPI
│   │   ├── api/v1/                   # routers, DTO y errores públicos
│   │   ├── domain/                   # entidades, unidades, estados, errores, puertos
│   │   ├── application/              # casos de uso y transacciones
│   │   ├── auth/                     # sesiones y capacidades por emergencia
│   │   ├── emergencies/ / zones/ / observations/
│   │   ├── resources/ / transport/ / profiles/
│   │   ├── prioritization/           # AHP, criterios, TOPSIS, incertidumbre, explicación
│   │   ├── gis/                      # elegibilidad, grafo, rutas, invalidación
│   │   ├── optimization/             # MIP F5, etapas, estados y extracción
│   │   ├── planning/                 # contratos de planes, factibilidad y evaluación comunes
│   │   ├── recommendations/          # revisión, decisión humana, reservas
│   │   ├── audit/                    # eventos inmutables y trazas
│   │   ├── experiments/
│   │   │   ├── generator/            # escenarios piloto/confirmatorio, máscaras
│   │   │   ├── baseline_fifo.py      # cola FIFO; no importa optimizador
│   │   │   ├── metrics.py            # KPI F7, usa evaluador H común
│   │   │   ├── pipeline.py           # orquestación pareada y fallos
│   │   │   └── exports.py            # CSV largo/pares, JSON, manifiestos
│   │   ├── db/                       # SQLAlchemy, repositorios, UoW, adapters
│   │   ├── jobs/                     # cola SQL persistente, worker, leases
│   │   ├── ui/                       # formularios y revisión; sin BI duplicado
│   │   │   ├── templates/            # Jinja2
│   │   │   └── static/               # CSS/HTMX versionados localmente
│   │   └── settings.py
│   └── tests/
│       ├── unit/                     # priorización, optimización, FIFO, KPI
│       ├── integration/              # PostgreSQL/PostGIS, API, jobs, GIS
│       ├── contracts/                # normalización explícita y exportaciones
│       ├── security/ / concurrency/ / system/
│       └── fixtures/                 # ejemplos/adaptadores; no cohorte principal
├── database/
│   ├── alembic.ini / migrations/versions/
│   ├── bootstrap/                    # bases y roles; sólo aprovisionamiento
│   └── views/analytics/              # SQL fuente de vistas, desplegado por migraciones
├── experiments/
│   ├── config/                       # perfiles/manifiestos aprobados
│   ├── fixtures/pilot/ / confirmatory/ / stress/
│   ├── oracle/                       # sólo generador/evaluador autorizado
│   ├── manifests/                    # intención, congelamiento, hashes
│   └── results/                      # por campaña inmutable, sin sobrescribir
├── metabase/
│   ├── dashboards.md                # catálogo de cinco dashboards/preguntas/filtros
│   └── verification/                # capturas y comprobación de permisos
├── docker/                          # Dockerfile API/worker compartido
├── scripts/                         # tareas de desarrollo/backup/restauración futuras
└── docs/                            # ocho documentos F8 + ADR/runbooks posteriores
```

## Límites y dependencias

El monolito modular mantiene un solo paquete y una sola imagen Python para API/worker; no son microservicios con modelos divergentes. Los routers convierten entradas, autentican y delegan. `application` coordina transacciones y repositorios; `domain` expresa estados e invariantes sin FastAPI/SQLAlchemy. Los módulos de negocio agrupan políticas por concepto. `db` contiene adaptadores, no fórmulas humanitarias.

`prioritization` recibe snapshots tipados y devuelve resultados puros, sin red ni escritura SQL. `optimization` recibe prioridades y rutas elegibles congeladas; no calcula permisos ni confirma decisiones. `planning/feasibility` verifica R01–R13 fuera del solver y se utiliza con SIPRE y FIFO. `planning/evaluation` es la única definición ejecutable de H/costo para comparar métodos; `experiments/metrics` añade KPI de F7. El validador no reutiliza restricciones internas del solver como única prueba de corrección.

`gis` prepara secuencias de arcos por tipo de vehículo/unidad y snapshot. `transport` administra activos/restricciones; el dominio no importa NetworkX. `recommendations` ejecuta una decisión explícita con autorización, validación y reservas en una única transacción. `audit` registra eventos en esa misma transacción cuando sean parte de la decisión.

`experiments/generator` puede crear el oracle, pero los DTO que reciben los algoritmos sólo contienen `observed_snapshot`. El proceso de ejecución no monta el directorio oracle ni recibe una sesión de BD con acceso a él. Evaluación retrospectiva separada y sin mezclar sus KPI con cobertura conocida.

## Responsabilidades de persistencia

| Esquema/base | Propietario funcional | Contenido |
|---|---|---|
| `core` | auth/jobs | usuarios, roles, sesiones, capacidades, jobs e idempotencia (extensiones técnicas propuestas) |
| `ops` | emergencies/observations/resources/transport | emergencias, reportes, necesidades, catálogo, ledger, stock, activos, reservas |
| `geo` | gis/zones | geometrías, nodos/arcos versionados, rutas y secuencias |
| `model` | profiles/prioritization | perfiles, snapshots, corridas, factores y resultados F4 |
| `planning` | optimization/recommendations | perfiles F5, corridas, asignaciones, déficits, recomendaciones y decisiones |
| `audit` | audit | eventos append-only sin secretos |
| `experiments` | experiments | escenarios, campañas, ejecuciones, métricas, hashes y estados |
| `analytics` | migraciones y vistas | doce vistas F6 y campos experimentales F7, sin lógica matemática duplicada |
| `metabase_app` (otra base) | Metabase | usuarios, preguntas, dashboards y configuración de BI |

Todas las modificaciones de esquemas y vistas se despliegan mediante Alembic, incluidos permisos cuando corresponda. Los archivos SQL de vistas no constituyen una segunda ruta manual de despliegue. El usuario migrador es distinto del usuario de aplicación y del lector Metabase.

## Convenciones previstas

Python en `snake_case`, clases en `PascalCase`, nombres de negocio y API consistentes con F6, explicaciones/documentación en español. IDs externos de fixtures se preservan junto a UUID internos. Fechas persistidas en UTC con offset, presentación `America/Santiago`. Dinero no forma parte de H; cantidades conservan unidad/precisión, scores usan doble precisión.

Los tests conservan IDs P4-Txx, P5-Txx y F7-xx en nombres o marcadores. Ninguna prueba confirmatoria corre en suite por defecto. Los artefactos finales se organizan por campaña y hash; nunca guardar contraseñas, `.env`, datos personales, dumps sensibles ni resultados mutables como fuente de verdad en Git. Versionar fixtures sintéticas pequeñas al congelar; resultados grandes sólo mediante manifiestos y ubicación local documentada.

La estructura evita duplicar FIFO entre `optimization` y `experiments` (el módulo común es `planning`), evita acoplar algoritmos a HTTP y permite pruebas en equipo sin infraestructura compleja. No se trasladan ni renombran documentos actuales en F8.
