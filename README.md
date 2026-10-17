# SIPRE — Sistema de Priorización y Optimización de Recursos en Post-Emergencia

Prototipo universitario chileno. **SIPRE recomienda; la autoridad humana decide.**

Estado actual: **Fase 9 validada técnicamente y pendiente de aprobación formal (`READY_FOR_REVIEW`)**. H1–H4 están implementados y verificados contra PostgreSQL/PostGIS real, incluidos Docker, migraciones, API, worker, autenticación, RBAC y auditoría. No se implementaron motores de decisión, ni simulador, ni experimentos confirmatorios (H5–H14). Véase [dictamen F9](docs/phase9-closeout.md).

## Qué funciona ahora

- API FastAPI completa de F9: CRUD con idempotencia, snapshots con fingerprint, cola de jobs durable y seed demostrativo, además de liveness y readiness PostgreSQL/PostGIS separadas (readiness exige PostGIS y el head de migración).
- Autenticación con sesiones Argon2id y CSRF, capacidades explícitas sin herencia de rol, auditoría persistente e inmutable, y un único envoltorio de error `{"error":{"code":...,"correlation_id":...}}`.
- Esquema completo con dominios, restricciones (desconocido con `NULL`, NaN/Inf, geometría 4326, inmutabilidad) y segregación por rol de base de datos.
- Compose con PostgreSQL/PostGIS, roles de conexión separados, migrador y Metabase opcional con base de aplicación independiente y lector restringido a vistas analytics.
- Entorno Python 3.12, lock universal `uv.lock` y exports con hashes para Docker.
- Credenciales locales aleatorias en `.env` ignorado por Git; imágenes fijadas por digest.
- Suite local: **37 pruebas aprobadas, 0 omitidas** con BD real; 19 checks E2E HTTP sin dobles y 16 verificaciones Docker, todas correctas.

## Requisitos y límites

Para contenedores: Docker Engine con contenedores Linux y Compose compatible con la Compose Specification; plataforma inicial `linux/amd64` (la imagen PostGIS fijada sólo declara esa plataforma). En esta entrega se habilitó y validó un runtime Docker sobre WSL (distro `SIPRE-F9-Validation`, Docker 29.x) para la verificación real; eso no modifica los requisitos mínimos declarados.

Para desarrollo local: Python 3.12 y `uv` 0.12.x. En esta máquina se utilizó el Python 3.12.14 provisto por el entorno de trabajo, sin instalarlo globalmente. `uv` ya estaba disponible y sustituye la propuesta inicial pip-tools, evitando instalar otro gestor. El contenedor instala desde exports con hashes mediante pip y no necesita uv en runtime.

## Arranque local con Docker, cuando esté disponible

Desde la raíz del repositorio, en PowerShell:

```powershell
# Sólo la primera vez; se niega a sobrescribir .env existente.
.\scripts\configure-local.ps1

# Validar sin imprimir las credenciales resueltas.
docker compose config --quiet
docker compose build api migrate
docker compose up -d api

# BI opcional; su setup inicial es independiente de usuarios SIPRE.
docker compose --profile bi up -d metabase
```

En la máquina de trabajo `.env` ya fue generado. No repetir configuración ni rotar contraseñas modificando sólo ese archivo: la inicialización de PostgreSQL ocurre únicamente con un volumen nuevo. No borrar el volumen para resolver credenciales. El bootstrap crea usuarios de BD, no usuarios del portal.

API: [liveness](http://127.0.0.1:8000/api/v1/health/live), [readiness](http://127.0.0.1:8000/api/v1/health/ready), [OpenAPI](http://127.0.0.1:8000/docs). Metabase: [setup local](http://127.0.0.1:3000). Los enlaces sólo responderán después de arrancar los servicios. PostgreSQL no publica puerto al host.

La migración `0001_namespaces` crea los namespaces F6 y las restricciones de acceso iniciales; las migraciones `0002`–`0004` añaden el esquema de negocio completo. La aplicación no tiene credenciales de superusuario/migración. El lector BI sólo tiene acceso al namespace analytics, con una vista de estado y sin escritura.

El servicio `worker-smoke` es una comprobación puntual, no un procesador de jobs:

```powershell
docker compose --profile check run --rm worker-smoke
```

## Desarrollo y pruebas

```powershell
uv sync --frozen --all-extras
uv pip check
uv run --frozen ruff check backend scripts database/migrations
uv run --frozen pytest -q --junitxml=artifacts/tests.xml
```

Si Python no está registrado, crear `.venv` con `uv venv --python RUTA_ABSOLUTA_A_PYTHON_3_12 .venv`. No usar SQLite como reemplazo de PostGIS para aprobar integración. Los tests HTTP corren en memoria, pero asyncio en Windows necesita sockets internos; en un sandbox restrictivo pueden requerir ejecución autorizada fuera de él.

Con una base real disponible, el wrapper local aísla credenciales y ejecuta la suite completa:

```powershell
.\scripts\local-runtime.py test
```

Las pruebas PostgreSQL requieren `SIPRE_TEST_DATABASE_URL` (y las variantes `SIPRE_TEST_APP_URL`, `SIPRE_TEST_WORKER_URL`, `SIPRE_TEST_READER_URL`) apuntando a una **base de prueba preparada** con el bootstrap y migración, como migrador. No crean ni destruyen bases automáticamente. Con la BD local se ejecutaron las 37 pruebas sin omisiones.

Para correr las pruebas en el contenedor (ya verificado contra la base real de validación):

```powershell
docker compose --profile test build tests
docker compose --profile test run --rm tests
```

Sin DB se puede inspeccionar la API localmente:

```powershell
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Liveness devolverá 200 y readiness 503. Esto es intencional, no una instalación completa. La aplicación no lee `.env` automáticamente: Compose lo utiliza para inyectar la URL adecuada. Para ejecutar API contra BD desde el host se necesita una URL accesible configurada expresamente; no usar por defecto el hostname interno `db`.

## Reproducibilidad y mantenimiento

`uv.lock` es el lock principal. Los archivos `requirements*.lock` son exportaciones derivadas, no se editan manualmente:

```powershell
uv export --frozen --no-dev --extra engines --no-emit-project --output-file requirements.lock --quiet
uv export --frozen --all-extras --no-emit-project --output-file requirements-dev.lock --quiet
```

`docker/images.lock.json` registra los manifiestos resueltos. `scripts/resolve-images.py` verifica disponibilidad por digest; `--write` requiere decisión explícita para actualizar. También actualizar referencias por defecto en Compose/Dockerfile y el entorno local, revisar y probar. Nunca actualizar en una campaña confirmatoria congelada.

NumPy/OR-Tools/NetworkX están instalados sólo para comprobar compatibilidad; el smoke SCIP resuelve un problema mixto mínimo ajeno a SIPRE. Eso no significa que las 17+28+26 pruebas matemáticas/experimentales estén implementadas o aprobadas.

## Próximas puertas

1. Ratificar F2/F3 y resolver las decisiones C01 (modo), C02 (estados) y C03 (DECISION_MAKER), que el equipo aún no ha aprobado formalmente.
2. Decidir el primer commit de referencia (G09); no se realizan commits automáticos.
3. Aceptar o rechazar el cierre de F9 con la evidencia presente. Sólo una aprobación humana explícita permite registrar `CLOSED_AFTER_APPROVAL`.
4. Entregar evidencia y pedir autorización antes de F10/motor de priorización (H5 en adelante).

Ver [estado F9](docs/phase9-status.md), [pauta y evidencias](docs/evaluation-rubric.md), [plan F8](docs/implementation-plan.md) y [decisiones](docs/risks-and-decisions.md). No se publicaron resultados experimentales ni se afirma validación operacional.

## Actualización de auditoría F9 — 2026-10-16

F2 y F3 ya están disponibles como `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md` en la raíz y fueron revisados completos. D01 queda subsanada en cuanto a recepción; ratificación y discrepancias quedan pendientes. H1–H4 están implementados y validados contra PostgreSQL/PostGIS real, incluidos Docker, migraciones, API, worker, autenticación, RBAC y auditoría. La Fase 9 queda en estado **`READY_FOR_REVIEW`**, pendiente de aprobación formal del equipo. Dictamen vigente: [docs/phase9-closeout.md](docs/phase9-closeout.md).

