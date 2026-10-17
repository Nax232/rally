# Fase 9 — Evidencia de pruebas

Fecha: 2026-10-16. Entorno Windows, Python local 3.12.14 y .venv; proyecto
`C:/Users/Matias/Downloads/Rally`. Postgres local aislado en `.tools/pgsql` (puerto 55439, base
`sipre`, data `.tools/phase9-db-live`). Las pruebas no certifican uso operacional real.

## Ejecución completa tras la implementación H1–H4

Comandos ejecutados desde la raíz (PowerShell) y en WSL:

| Comando exacto | Resultado observado | Qué acredita |
|---|---|---|
| `.venv\Scripts\python.exe -m ruff check backend scripts database/migrations` | exit 0; All checks passed! | Reglas estáticas configuradas |
| `.venv\Scripts\python.exe scripts\local-runtime.py test` | exit 0; **37 passed, 0 skipped, 4 warnings** | Suite completa con BD real: unitarias, contratos e integración |
| `wsl -d SIPRE-F9-Validation -- sh artifacts/phase9-docker-validate.sh` | exit 0; **16 correctas, 0 fallos** | Docker real: servicios, segregación, backup/restore, migraciones y suite en contenedor |
| `wsl -d SIPRE-F9-Validation -- sh artifacts/phase9-e2e-run.sh` | exit 0; **19 correctas, 0 fallos** | Flujo HTTP end-to-end sin dobles de prueba |

La ejecución pytest en Windows se realizó fuera del sandbox con autorización porque una ejecución
previa quedó bloqueada en el socket interno asyncio. Con la BD local disponible no hubo omisiones.

JUnit local: [phase9-complete-tests.xml](../artifacts/phase9-complete-tests.xml), ignorado por Git.

## Cobertura efectiva

- `test_infrastructure_api.py` (unitarias): liveness; 503 sin BD; readiness feliz con conexión
  simulada; error de conexión sin exponer credenciales; correlación UUID; validación de settings y
  representación de secretos; contrato único de error para 503.
- `test_dependency_smoke.py`: OR-Tools SCIP ejecuta un problema mixto genérico mínimo con óptimo
  2.5. No implementa ni verifica F5.
- `test_delivery_invariants.py`: hashes de seis archivos F7, puertos locales y digests de imágenes.
- `test_postgres_foundation.py`: PostGIS, head de migración, ocho namespaces y privilegios reales
  del lector BI (sin acceso a esquemas de dominio ni CREATE).
- `test_foundation_api.py` (integración, BD real): desconocido vs cero, permisos y CSRF, ámbito por
  emergencia, idempotencia, stock y activos, informes y fechas, snapshots e historial, permisos SQL
  reales e inmutabilidad, negativos/NaN/CRS, reclamo de job vencido, revocación y no fuga de
  credenciales, sobretiro concurrente, límite de login, contrato de error y listado de usuarios,
  material de contraseña ausente, conflicto de revisión y aislamiento de snapshot, rutas de fallo
  del worker (`SNAPSHOT_HASH_MISMATCH`, `MAX_ATTEMPTS`) y poda de sesiones expiradas.

Advertencias: tres DeprecationWarning de tipos SWIG sin `__module__`; una StarletteDeprecationWarning
sobre TestClient con httpx (sugiere httpx2). No ocultadas; no fueron fallos.

## Verificaciones Docker y E2E ejecutadas

| Verificación | Resultado |
|---|---|
| Liveness y readiness tras reinicio de servicios | Correctas |
| Alembic head `0004_snapshot_lock` tras reinicio | Correcto |
| Lector BI con SELECT sobre vista analytics y denegado en tablas de dominio/escritura | Correcto |
| `sipre_app` denegado en borrar `audit.events` y alterar `inventory_balances` | Correcto |
| `sipre_worker` denegado en crear usuarios | Correcto |
| Backup/restore en base nueva sin pérdida (emergencias y eventos conservados) | Correcto |
| Migración desde base vacía hasta head (26 tablas) | Correcta |
| Upgrade desde `0003_integrity` a `0004_snapshot_lock` | Correcto |
| Worker `--once` en contenedor | Correcto |
| Suite completa en contenedor | **37 passed** |
| Flujo E2E HTTP: login, creación VIEWER, 403 por rol, 403 sin CSRF, 401 sin sesión, emergencia, fuente, zona MultiPolygon 4326, tipo de recurso, necesidad UNKNOWN con NULL, idempotencia sin duplicados, snapshot con fingerprint, job 202 y 501 explícito | **19/19** |

## Verificaciones previas de la misma entrega F9

| Comando / validación | Resultado y limitación |
|---|---|
| `uv lock`; `uv sync --frozen --all-extras` | Instalación de 46 paquetes completada |
| `uv pip check` | 46 paquetes compatibles según metadatos |
| `alembic upgrade head --sql` (offline) | SQL generado en `artifacts/phase9-schema.sql` |
| `bash -n database/bootstrap/10-databases.sh` | exit 0; sólo sintaxis shell |
| `git check-ignore .env .venv .cache .tools artifacts` | Todos ignorados |
| Verificación SHA-256 CLI Compose | `8aeaa0055e660e12cf07cd70680dc8333957fe6718528b91ec3da084eab62483` |

## Pruebas futuras que siguen fuera del alcance de F9

Las 17 pruebas F4, 28 F5 y 26 F7 están planificadas para sus hitos (71 casos fuente). No se
ejecutaron ni se sustituyeron por estas 37. No se generaron escenarios definitivos ni se ejecutó
confirmatorio. La validación de rutas bloqueadas, factibilidad logística completa y decisión
humana atómica se realiza al implementar H7/H6/H8.

## Conservación verificada

F2 mantiene SHA-256 `f6a0fe0946783439984d7ecada000e844a989be1f788954b1168de111c522cb5`; F3 mantiene
`c649954705ac844612a7679a899e8547e25370bddcb6459fd56aa14965dcf6ee`. No se hicieron commits.
