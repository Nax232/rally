# Fase 10 — Evidencia de validación observada

Fecha: 2026-10-17. Entorno local: Python 3.12, PostgreSQL/PostGIS real en base
aislada `sipre`; Docker Engine 29.8.2 sobre WSL, Compose con imágenes locales F10.
No se ejecutaron simulaciones confirmatorias ni se certificó uso operacional.

| Comando / comprobación | Resultado observado |
|---|---|
| `.venv\\Scripts\\python.exe scripts/local-runtime.py migrate` | Upgrade incremental desde `0006` hasta `0008_simulated_assistance` correcto |
| `.venv\\Scripts\\python.exe scripts/local-runtime.py test` | **69 passed, 4 warnings**; cero omitidas; integración con PostgreSQL/PostGIS real |
| `.venv\\Scripts\\ruff.exe check backend scripts database/migrations` | Todos los checks pasaron |
| `uv pip check` | 50 paquetes compatibles; el intento en sandbox falló por caché de uv y se repitió con autorización |
| `docker compose ... build api migrate worker tests` | Imágenes locales `sipre-api:phase10` y `sipre-tests:phase10` construidas |
| `docker compose ... up -d api worker` | DB saludable, migrador terminó, API y worker iniciados |
| `sh scripts/validate-phase9-compose.sh .tools/compose-validation.env sipre-f9-validation` | **17/17**: readiness y head `0008`, segregación BI, respaldo/restauración, migración vacía, upgrade `0003`→`0008`, worker y **69 pruebas en contenedor** (1 warning) |
| `sh scripts/run-phase9-e2e.sh .tools/compose-validation.env sipre-f9-validation` | **21/21**: autenticación/RBAC, datos, snapshot, job, F4 202 y resultado del worker por HTTP |

El script mantiene su nombre histórico `phase9` y ahora incluye dos verificaciones F10.
Las bases temporales del verificador Compose se crean con nombres propios y se eliminan
al terminar; la base principal no se borra. El stack Docker usado es sólo de validación.

## Correspondencia con las pruebas F4

| ID | Evidencia ejecutada | Resultado |
|---|---|---|
| P4-T01 | `test_p4_t01_t02_t03_ahp_gates` | Pesos DEMO y CR≈0 |
| P4-T02 | mismo test | CR>0.10 rechazado |
| P4-T03 | mismo test | matriz inválida rechazada |
| P4-T04 | `test_p4_t04_t05_extremes_and_fixture` | ceros/unos → 0/1 |
| P4-T05 | mismo test | fixture Z01>Z03>Z02, ≤1e-5 |
| P4-T06 | `test_p4_t06_t07_t14_anchored_monotonic_and_deterministic` | agregar zona conserva score absoluto |
| P4-T07 | mismo test | aumento de un criterio no reduce score |
| P4-T08 | `test_p4_t08_t09_t12_missing_distinct_from_zero_and_fixed_u` | NULL y cero observado diferentes |
| P4-T09 | mismo test; `test_priority_job_persists_exploratory_results_without_decisions` | sin reportes: verificación, intervalo, evidencia insuficiente |
| P4-T10 | `test_p4_t10_t11_uncertainty_and_elapsed_facts`, `test_f4_null_age_conflict_and_time_since_emergency` | U aumenta con antigüedad/falta y conflicto normalizado |
| P4-T11 | mismos tests; `test_f4_partial_assistance_preserves_clock_and_full_cover_zero`, `test_simulated_assistance_is_bounded_and_c7_preserves_unserved_time` | tiempo por hechos, parcial conserva reloj, total → 0 |
| P4-T12 | `test_p4_t08_t09_t12_missing_distinct_from_zero_and_fixed_u` | límite inferior≤estimado≤superior, U fijo |
| P4-T13 | `test_p4_t13_t16_t17_explanation_profiles_no_dispatch` | distancias recompuestas de ocho factores |
| P4-T14 | `test_p4_t14_tie_group_is_deterministic_and_nontransitive_safe` | orden estable en empate ≤1e-9 |
| P4-T15 | `test_priority_job_persists_exploratory_results_without_decisions` | rechaza snapshot de otra emergencia; FK compuesta |
| P4-T16 | mismo test y `test_p4_t13_t16_t17_explanation_profiles_no_dispatch` | perfil ausente/error y pesos inválidos rechazados |
| P4-T17 | mismos tests de integración, ausencia de tabla `planning.decisions` | sin decisión confirmada, orden o despacho |

También se verificaron estado estimado/no confirmado de C5, contradicción con candidato
verificado, valores fraccionales fuera de dominio, perfil/resultado inmutable, RBAC,
idempotencia, segregación BI y limitación de asistencia efectiva por necesidad.

## Límite de esta evidencia

La implementación aún **no cumple por completo** el contrato F6 de tablas y API para
perfiles de criterios, AHP y clasificación por ID. El perfil completo está versionado y
congelado en cada corrida, pero D06 sólo autorizó **proponer** sus números sintéticos,
sujetos a revisión. La ejecución de una migración adicional de perfiles fue rechazada
por permisos del entorno; se retiró de la cadena activa, sin afirmar que hubiese pasado.
Por ello esta evidencia no basta para declarar F10 cerrada.
