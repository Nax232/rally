# Fase 9 — Análisis de brechas

Fecha de actualización: 2026-10-17. Revisión tras la implementación y validación de H1–H4. Severidad
bloqueante se refiere al cierre F9, no a certificar operación real.

## Inventario y alcance

Repositorio local en main, con commits y remoto `origin`. Código inspeccionado: `backend/app`,
`backend/tests`, `database/bootstrap`, `database/migrations`, `scripts`, `docker/Dockerfile`,
`compose.yaml`, `pyproject.toml` y locks. F2/F3 están como Markdown en la raíz y fueron
auditados. D01 queda subsanada por recepción; ratificación y discrepancias siguen pendientes.

F9 tiene alcance en F6 §14 y F8 H1–H4. H1–H4 están implementados y validados contra
PostgreSQL/PostGIS real, incluidos Docker, migraciones, API, worker, auth/RBAC y auditoría. No se
confunde fase 9 con hito 9 de UI.

## Brechas priorizadas y estado

| ID / prioridad | Hallazgo y requisito | Archivos | Estado |
|---|---|---|---|
| G01 bloqueante | Sin ejecución Docker/PostGIS real; RNF-011/012 | compose.yaml, Dockerfile, bootstrap, migraciones, tests | **Resuelta**: build, arranque, migración online, persistencia y restauración verificados en WSL/Docker (17/17) |
| G02 bloqueante | Entidades de dominio y constraints; RF-001–017, RQD, RNF-004/013 | migraciones, db | **Resuelta**: esquema completo con dominios, FKs, checks y triggers; migración desde vacía y upgrade verificados |
| G03 bloqueante | API dominio, jobs durables y seed; H3 y F6 F9 | api, worker, bootstrap | **Resuelta**: CRUD idempotente, snapshots, cola SQL durable, worker con verificación y seed SIMULATED; 501 explícito en motores |
| G04 bloqueante | Usuarios, sesiones, RBAC y auditoría; RNF-005/006/007, RF-058 | security, api, migraciones | **Resuelta**: sesiones Argon2id+CSRF, capacidades sin herencia, auditoría inmutable; 401/403/409/422/429/501 verificados |
| G05 alta | Segregación BI definida pero no demostrada | bootstrap, migraciones, tests | **Resuelta**: lector BI SELECT sobre vista analytics y denegado en dominio/escritura; `sipre_app` y `sipre_worker` con privilegios mínimos verificados |
| G06 alta | Historia y recuperación sin prueba | migraciones, tests | **Resuelta**: inmutabilidad SQL verificada, cierre de emergencia sin edición ordinaria, backup/restore y upgrade comprobados |
| G07 media | Readiness no valida revisión Alembic | db/health.py, tests | **Resuelta**: readiness exige PostGIS **y** head `0006_route_invalidation`; liveness separada |
| G08 baja | Cuatro advertencias dependencias | locks, test client | **Abierta**: SWIG y TestClient HTTPX deprecados no fallan; actualizar en tarea posterior con tests, sin tocar locks ahora |
| G09 media | Sin commit de referencia | Git | **Resuelta por evolución del repositorio**: existe historia y remoto; no se crea commit en esta revisión |
| G10 alta | El trigger de inmutabilidad de arcos candidatos impedía la invalidación al bloquear una vía en Docker | migraciones, GIS, tests | **Resuelta**: migración incremental `0006`, revocación DELETE directo y 51/51 pruebas Docker |
| G11 media | Evidencia F9 y trazabilidad mencionaban 37 pruebas, head `0004` y H7 pendiente | README, docs, scripts | **Resuelta**: se registra la ejecución 51/51, 17/17 Compose, 19/19 HTTP y H7 implementado por separado |

## Contradicciones y refinamientos

| ID / tipo | Fuentes y diferencia | Estado |
|---|---|---|
| C01 modo | F3 admite SIMULATED y OPERATIONAL_RECORD; F6 y settings sólo SIMULATED | **Resuelta por el usuario**: mantener sólo SIMULATED en este prototipo; documentar la excepción al SRS para eventual revisión formal |
| C02 estados | F3 define cuatro estados; JSON F6 añade derivados de análisis | **Refinamiento**, no contradicción: emergencia usa DRAFT/ACTIVE/CLOSED/CANCELLED; análisis y planes conservan sus estados propios |
| C03 rol | DECIDER (F3) vs DECISION_MAKER (F6) | **Refinamiento técnico**: `DECISION_MAKER` implementa la función DECIDER sin herencia de ADMIN; la autoridad humana sigue obligatoria |
| C04–C08 | Estados de recomendación, invalidación, campos SRS, errores solver, grupos BI | Corresponden a H6/H8/H10; fuera de F9 |
| D03 experimental | Presupuesto confirmatorio vs piloto | Abierta; no bloquea infraestructura F9 |

F4/F5 siguen siendo fuentes matemáticas; F7 mantiene cuatro familias, doce semillas, 48 instancias
y 96 ejecuciones pareadas. Ningún cambio ni experimento efectuado.

## Secuencia recomendada para el cierre

1. El equipo revisa la excepción `SIMULATED` y los refinamientos C02/C03 en el dictamen.
2. Con la evidencia presente, acepta o rechaza el cierre. Sólo una aprobación explícita permite registrar
   `CLOSED_AFTER_APPROVAL`.

Esta es una propuesta revisable. No autoriza cambios sensibles ni amplía F9 a algoritmos, UI,
dashboards o confirmatorio.
