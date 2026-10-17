# SIPRE — Registro de avance Fase 9

Fecha de actualización: 2026-10-17. **Fase 9 cerrada tras aprobación humana explícita**
(`CLOSED_AFTER_APPROVAL`, 2026-10-17). H1–H4 están
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
| Git local | `.git`, `.gitignore`, `.gitattributes` | Rama main con commits y remoto `origin`; cambios correctivos locales aún sin commit |
| Python | `pyproject.toml`, `uv.lock`, locks | 46 paquetes en `.venv`; sin cambios globales |
| API | `backend/app/main.py`, `api.py`, `security.py`, `schemas.py`, `worker.py`, `bootstrap.py`, `db/health.py` | Liveness/readiness, CRUD con idempotencia, snapshots, jobs, sesiones, RBAC y auditoría |
| Contenedores | `compose.yaml`, `docker/Dockerfile`, `docker/images.lock.json` | Build, arranque, reinicio y persistencia validados en WSL/Docker |
| Bases y roles | `database/bootstrap/10-databases.sh` | Dos bases y roles separados (app/worker/lector/BI); ejecutado y verificado |
| Migraciones | `database/migrations/versions/0001..0006`, SQL de fundación y GIS | Esquema con dominios, triggers de inmutabilidad/auditoría/stock, red GIS e invalidación de rutas |
| Configuración | `scripts/configure-local.ps1`, `.env.example`, `scripts/local-runtime.py` | Credenciales aleatorias en `.env` ignorado; nunca se imprimen |
| Pruebas | `backend/tests/` | 51 aprobadas, 0 omitidas con BD real en Windows y Docker; 19 checks E2E HTTP sin dobles |

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
| `python scripts/local-runtime.py test` | **51 passed, 0 skipped**, 4 advertencias de dependencias |
| Smoke OR-Tools/SCIP | Problema mixto mínimo obtiene 2.5; no es modelo SIPRE F5 |
| Compose `config --quiet` | Configuración resuelta válida, sin imprimir secretos |
| `sh scripts/validate-phase9-compose.sh .tools/compose-validation.env sipre-f9-validation` | **17 correctas, 0 fallos**: liveness/readiness, alembic head `0006`, segregación BI, backup/restore, migración desde BD vacía, upgrade `0003`→`0006`, worker y suite completa en contenedor |
| `sh scripts/run-phase9-e2e.sh .tools/compose-validation.env sipre-f9-validation` | **19 correctas, 0 fallos**: login, RBAC, CSRF, idempotencia, zona MultiPolygon 4326, necesidad UNKNOWN con NULL, snapshot con fingerprint, job 202 y 501 explícito en motores |

Las rutas H7 están implementadas y verificadas por separado. Una prueba Docker inicialmente
falló porque el trigger inmutable impedía la cascada de invalidación; la migración `0006` la
corrigió y la suite completa pasó de nuevo. La evidencia actual está en
[phase9-test-evidence.md](phase9-test-evidence.md).

JUnit en `artifacts/` local, ignorado por Git. Las pruebas BD se omiten sólo si falta
`SIPRE_TEST_DATABASE_URL`; con la BD local disponible se ejecutaron completas. Readiness feliz se
prueba con conexión simulada en unitarias **y** contra servidor real en integración.

Cuatro advertencias persisten (tres SWIG/OR-Tools y una deprecación de HTTPX en TestClient); no se
ocultaron ni implican fallo. Actualizar el cliente de tests al revisar dependencias, no durante
este experimento congelado.

## Cierre aprobado

1. Confirmar la excepción SRS ya elegida por el usuario: sólo SIMULATED; C02/C03 son refinamientos
   documentados en [brechas](phase9-gap-analysis.md).
2. El usuario aceptó el cierre con la evidencia presente y autorizó iniciar F10/H5.

D01 queda subsanada por recepción de F2/F3. D24 queda subsanada: el runtime Docker sí se habilitó
y validó. D03 y las decisiones matemáticas/experimentales permanecen sin cambios.

## Referencias técnicas consultadas

- [Docker: orden de arranque](https://docs.docker.com/compose/how-tos/startup-order/)
- [PostGIS: imágenes](https://hub.docker.com/r/postgis/postgis/tags)
- [Metabase v0.64.1](https://github.com/metabase/metabase/releases/tag/v0.64.1)
- [Compose: releases oficiales](https://github.com/docker/compose/releases)

Fase 9 queda **cerrada tras aprobación humana**; no se certifica para uso
real ni constituye cierre automático.
