# SIPRE — Dependencias, versiones y compatibilidad previstas

Fecha de consulta: 2026-10-16. Estado: **selección candidata de planificación; ninguna dependencia instalada o combinación certificada en F8**. Los parches exactos y digests se fijan en H1 después de resolver dependencias y probar imágenes. No usar `latest` en la entrega reproducible ni confundir rama propuesta con versión instalada.

Actualización F9: la tabla siguiente conserva la propuesta histórica F8. Las versiones efectivamente resueltas están en `../uv.lock`, los exports Docker en `../requirements*.lock` y las imágenes por digest en `../docker/images.lock.json`. Se usó uv 0.12.6 ya instalado en lugar de añadir pip-tools; se validó Compose con CLI oficial v5.6.0 sin daemon. Compatibilidad Python/SCIP comprobada localmente; build/despliegue Linux pendiente. Resultados exactos en [phase9-status.md](phase9-status.md).

## Base tecnológica

| Componente | Versión/línea candidata | Motivo y compatibilidad a verificar | Hito |
|---|---|---|---|
| CPython | 3.12.x, parche mantenido y fijado en imagen Debian slim | Base conservadora con wheels científicos; soporte del SO/arquitectura y OR-Tools se comprueba en build | H1 |
| FastAPI / Uvicorn | FastAPI 0.136.x como candidato revisado; Uvicorn estable compatible fijado al resolver | ASGI y API tipada; no fijar Starlette manualmente contra restricciones de FastAPI | H1/H3 |
| Pydantic / pydantic-settings | 2.x | DTO y configuración; no mezclar modelos v1; validación finita, unidades y fechas | H1/H3 |
| SQLAlchemy / Alembic | 2.0.x / 1.x | Persistencia y migraciones versionadas, sin `create_all` como estrategia de actualización | H1/H2 |
| psycopg | 3.x, wheel compatible fijado | Driver PostgreSQL utilizado por SQLAlchemy; transacciones síncronas para MVP | H1/H2 |
| PostgreSQL | 16.x mantenida, parche/digest fijados | Base común operacional y DB Metabase; extensiones sólo en `sipre` | H1/H2 |
| PostGIS | 3.5.x estable sobre PostgreSQL 16 | Candidato de extensión; imagen `postgis/postgis` que combine ambos, etiqueta exacta pendiente de comprobación | H1/H2 |
| NumPy | 2.x compatible con OR-Tools fijado por resolver | Doble precisión y cálculo vectorial; no agregar SciPy para AHP geométrico | H1/H5 |
| OR-Tools | 9.15.x candidata | `linear_solver`/MPSolver con backend SCIP; probar disponibilidad real y variables continuas/enteras | H1/H6 |
| SCIP | Versión del backend distribuido por build OR-Tools elegido | Registrar `SolverVersion`, licencias y tolerancias efectivas; no asumir versión de backend igual a OR-Tools | H6 |
| NetworkX | 3.7.x candidata | Grafo dirigido, rutas de escenario; Python 3.12 compatible según documentación consultada | H1/H7 |
| Jinja2 / HTMX | 3.1.x / 2.x candidatos | Portal transaccional liviano; assets locales con versión/hash; sin toolchain Node obligatoria | H9 |
| Argon2 | `argon2-cffi` estable compatible, pin al resolver | Hash de contraseñas requerido por F6; parámetros medidos en equipo y librería mantenida | H4 |
| Metabase OSS | Release estable OSS `v0.*`, etiqueta exacta y digest a seleccionar en H1 | Imagen `metabase/metabase`; no Enterprise, H2 ni funciones de pago como dependencia | H1/H10 |
| Docker Engine + Compose | Engine estable soportado por host + Compose v2 | Contenedores Linux locales, volúmenes, health checks; validar WSL2/virtualización si se usa Windows | H1 |
| pytest / HTTPX / pytest-cov | Releases estables compatibles fijadas en lock de desarrollo | Tests numéricos, API, BD y reporte; no usar SQLite para probar semántica PostGIS/concurrencia | H1–H12 |
| pip-tools (sólo desarrollo) | Release estable compatible fijada | Generar locks con hashes desde `pyproject.toml`; única herramienta adicional de resolución propuesta | H1 |

Las líneas propuestas son un punto de partida reproducible, no una afirmación de que sean las versiones más recientes. Si el resolver o revisión de mantenimiento rechaza una línea, registrar alternativa y motivo antes de congelar; un cambio de backend/tolerancia que afecte resultados requiere aprobación. Metabase y bibliotecas auxiliares tienen pin exacto pendiente porque no se ha instalado ni probado un conjunto. Esta condición impide llamar al stack «validado en ejecución».

## Fuentes primarias y alcance de evidencia

- [Versiones de Python](https://devguide.python.org/versions/): comprobar ciclo de soporte al congelar la imagen; no depender del alias WindowsApps detectado.
- [FastAPI: notas de versión](https://fastapi.tiangolo.com/release-notes/): la línea consultada documenta Pydantic v2. Las transitivas deben resolverse juntas.
- [SQLAlchemy: dialecto PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html): respalda el uso del dialecto con psycopg y mecanismos de transacción; no demuestra compatibilidad del proyecto todavía.
- [PostgreSQL: política de versiones](https://www.postgresql.org/support/versioning/): la rama 16 está soportada; elegir parche mantenido al construir, sin congelar uno sólo por una captura web.
- [PostGIS 3.5: instalación](https://postgis.net/docs/manual-3.5/postgis_installation.html): PostgreSQL 16 está dentro del rango descrito. El manual puede mostrar desarrollo; seleccionar release estable, no `dev`.
- [OR-Tools: releases](https://github.com/google/or-tools/releases): se encontró v9.15; [instalación](https://developers.google.com/optimization/install) y [MIP](https://developers.google.com/optimization/mip/mip_example) orientan la comprobación binaria. Google recomienda SCIP para problemas mixtos con variables continuas y enteras. Por ello se propone SCIP; no convertir litros a enteros para usar CP-SAT sin aprobación matemática.
- [NetworkX: instalación](https://networkx.org/documentation/stable/install.html): la documentación 3.7 consultada admite Python 3.12–3.14. Instalar paquete base; extras científicos no necesarios para caminos mínimos.
- [Metabase: Docker](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker) y [DB de aplicación](https://www.metabase.com/docs/latest/installation-and-operation/configuring-application-database): imagen oficial y base PostgreSQL separada para configuración. La arquitectura SIPRE restringe además la conexión de datos a vistas `analytics`.

Estas fuentes verifican disponibilidad conceptual y compatibilidad declarada; los documentos del proyecto siguen siendo autoridad sobre reglas de negocio y modelos.

## Dependencias evitadas o condicionadas

No se requieren Redis/Celery, Kubernetes, servicios GIS comerciales, frontend React, nube, GPU, LLM, SDK institucional ni segundo dashboard. Cola y sesiones se respaldan en PostgreSQL. CSV, JSON, hashes, UUID, fechas y estadísticas descriptivas simples utilizan biblioteca estándar/NumPy.

PostGIS procesa validación/medición espacial desde SQL; inicialmente no se exige GeoPandas/GDAL en Python ni pgRouting. GeoAlchemy2 sólo se añadiría si su adaptación ORM reduce complejidad de forma demostrable; no está asumida en este plan. OSM es opcional y no equivale a verificación vial; la red sintética de F6/F7 basta para experimento aprobado.

No imponer JSON Schema como biblioteca extra: los contratos descriptivos actuales se formalizarán con modelos tipados y exportación versionada. Herramientas de análisis de vulnerabilidades/formato pueden seleccionarse en H1 con justificación y lock, sin sumarlas silenciosamente al runtime.

## Validación de compatibilidad en H1/H2

1. Registrar OS, arquitectura CPU, Docker/Compose, recursos asignados, runtime e imágenes. Verificar Python 3.12 dentro del contenedor; no necesitar instalación global en host.
2. Resolver dependencias en Linux objetivo, generar locks con hashes, instalar desde cero y ejecutar `python -m pip check`. Guardar log de resolución y versiones efectivas, incluidas NumPy, protobuf y demás transitivas de OR-Tools.
3. Importar FastAPI/Pydantic/SQLAlchemy/psycopg/NumPy/OR-Tools/NetworkX. Probar instancia SCIP y un problema mixto mínimo con solución conocida; es smoke de compatibilidad, no implementación del modelo SIPRE.
4. Iniciar PostgreSQL/PostGIS, comprobar versión/extensión y conexión psycopg; migración mínima H2. Validar UTF-8, `timestamptz`, UUID/JSONB/NUMERIC y geometría SRID.
5. Iniciar Metabase OSS con DB `metabase_app`, persistir configuración y reiniciar sin pérdida; en H10 verificar acceso de lectura a vistas y rechazo de escritura.
6. Congelar lock, etiquetas/digests, plataforma y evidencia; no descargar actualizaciones durante confirmatorio. Actualización posterior produce nuevo entorno/campaña.

No se ejecutó ninguno de estos pasos en F8. No existe lock generado ni una imagen construida.

## Recursos y sostenibilidad

Presupuesto de ingeniería **propuesto, no mínimo validado**: equipo de 4 núcleos, 8 GB RAM disponibles como objetivo inicial (16 GB facilita coexistir con otras aplicaciones), 20 GB libres para imágenes/volúmenes/evidencias. Comenzar con un worker y una corrida solver a la vez; limitar hilos y documentar cargas concurrentes. Medir RAM real de Metabase/JVM, Postgres y solver en piloto antes de ajustar contenedores. El hardware del usuario no ha sido inventariado exhaustivamente.

Preferir una instancia Postgres con bases separadas en demo; la separación de roles y credenciales sigue siendo obligatoria. No prometer alta disponibilidad o RPO/RTO no ensayados. Software principal abierto/gratuito; revisar términos del empaquetado Docker que adopte la universidad, licencias de imágenes y recursos. No se presupone costo cero de hardware, electricidad, administración o tiempo humano. No se contrató servicio alguno.
