# SIPRE — Registro de avance Fase 9

Fecha: 2026-10-16 (actualizado tras la ejecución completa de H1–H4). **Fase 9 implementada y
validada técnicamente; el cierre formal sigue pendiente de aprobación humana.** H1–H4 están
entregados y verificados contra PostgreSQL/PostGIS real, incluidos Docker, migraciones, API,
worker, autenticación, RBAC y auditoría. Este registro conserva el contexto de la auditoría previa;
el estado vigente es el [dictamen de cierre](phase9-closeout.md).

## Autorización y alcance

El usuario solicitó «Continua con la fase 9». F6 §14 define F9 como Compose/Postgres/PostGIS,
migraciones, auth/RBAC, entidades base y seed sintético, es decir H1–H4 del plan F8. F2/F3 fueron
recibidos como `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md` y auditados contra F4–F7. No se avanzó
a F10 ni a motores de decisión. Fase 9 no equivale al Hito 9 de interfaz.

## Implementación entregada

| Área | Archivos | Estado |
|---|---|---|
| Git local | `.git`, `.gitignore`, `.gitattributes` | Rama main inicializada, sin commits/remotos |
| Python | `pyproject.toml`, `uv.lock`, locks | 46 paquetes en `.venv`; sin cambios globales |
| API | `backend/app/main.py`, `api.py`, `security.py`, `schemas.py`, `worker.py`, `bootstrap.py`, `db/health.py` | Liveness/readiness, CRUD con idempotencia, snapshots, jobs, sesiones, RBAC y auditoría |
| Contenedores | `compose.yaml`, `docker/Dockerfile`, `docker/images.lock.json` | Build, arranque, reinicio y persistencia validados en WSL/Docker |
| Bases y roles | `database/bootstrap/10-databases.sh` | Dos bases y roles separados (app/worker/lector/BI); ejecutado y verificado |
| Migraciones | `database/migrations/versions/0001..0004`, `sql/0002_foundation.sql` | Esquema completo con dominios, triggers de inmutabilidad/auditoría/stock y segregación por rol |
| Configuración | `scripts/configure-local.ps1`, `.env.example`, `scripts/local-runtime.py` | Credenciales aleatorias en `.env` ignorado; nunca se imprimen |
| Pruebas | `backend/tests/` | 37 aprobadas, 0 omitidas con BD real; 19 checks E2E HTTP sin dobles |

`worker-smoke` comprueba conexión una vez; no sustituye al worker funcional de `app/worker.py`, que
sí está implementado y probado. Metabase corre bajo perfil `bi` con lector restringido a vistas
analytics; los dashboards de negocio pertenecen a H10.

## Versiones observadas

Python 3.12.14; uv 0.12.6; FastAPI 0.136.3; Pydantic 2.14.1; SQLAlchemy 2.0.55; Alembic 1.20.0;
psycopg 3.3.6; NumPy 2.5.4; OR-Tools 9.15.6755; NetworkX 3.7; pytest 9.1.1. Todas las transitivas
están en `uv.lock`.

Imágenes: Python 3.12.14 slim-bookworm, PostGIS 16-3.5, Metabase OSS v0.64.1, fijadas por digest
en `docker/images.lock.json`; plataforma linux/amd64.

Se utilizó uv preexistente en lugar de pip-tools propuesto en F8. Se usó la CLI oficial Compose en
`.tools/compose` (ignorada por Git) para validar configuración sin daemon. El plan F8 decía
Compose v2: se conserva la Compose Specification y se registra la versión efectivamente usada.

## Evidencia y pruebas

| Comando / comprobación | Resultado |
|---|---|
| `ruff check backend scripts database/migrations` | Sin errores |
| `python scripts/local-runtime.py test` | **37 passed, 0 skipped**, 4 advertencias de dependencias |
| Smoke OR-Tools/SCIP | Problema mixto mínimo obtiene 2.5; no es modelo SIPRE F5 |
| Compose `config --quiet` | Configuración resuelta válida, sin imprimir secretos |
| `sh artifacts/phase9-docker-validate.sh` | **16 correctas, 0 fallos**: liveness/readiness, alembic head `0004_snapshot_lock`, segregación BI y privilegios reales, backup/restore, migración desde BD vacía, upgrade `0003`→`0004`, worker y suite completa en contenedor |
| `sh artifacts/phase9-e2e-run.sh` | **19 correctas, 0 fallos**: login, RBAC, CSRF, idempotencia, zona MultiPolygon 4326, necesidad UNKNOWN con NULL, snapshot con fingerprint, job 202 y 501 explícito en motores |

JUnit en `artifacts/` local, ignorado por Git. Las pruebas BD se omiten sólo si falta
`SIPRE_TEST_DATABASE_URL`; con la BD local disponible se ejecutaron completas. Readiness feliz se
prueba con conexión simulada en unitarias **y** contra servidor real en integración.

Cuatro advertencias persisten (tres SWIG/OR-Tools y una deprecación de HTTPX en TestClient); no se
ocultaron ni implican fallo. Actualizar el cliente de tests al revisar dependencias, no durante
este experimento congelado.

## Cierre pendiente

1. Ratificación del equipo sobre F2/F3 y resolución registrada de C01 (modo), C02 (estados de
   emergencia) y C03 (DECISION_MAKER). Se conserva SIMULATED y los cuatro estados propuestos.
2. Decisión humana sobre el primer commit de referencia (G09): no se realizan commits automáticos.
3. Aceptar o rechazar el cierre con la evidencia presente. Sólo una aprobación explícita permite
   registrar `CLOSED_AFTER_APPROVAL`.

D01 queda subsanada por recepción de F2/F3. D24 queda subsanada: el runtime Docker sí se habilitó
y validó. D03 y las decisiones matemáticas/experimentales permanecen sin cambios.

## Referencias técnicas consultadas

- [Docker: orden de arranque](https://docs.docker.com/compose/how-tos/startup-order/)
- [PostGIS: imágenes](https://hub.docker.com/r/postgis/postgis/tags)
- [Metabase v0.64.1](https://github.com/metabase/metabase/releases/tag/v0.64.1)
- [Compose: releases oficiales](https://github.com/docker/compose/releases)

Fase 9 queda **validada técnicamente y pendiente de aprobación formal**; no se certifica para uso
real ni constituye cierre automático.
