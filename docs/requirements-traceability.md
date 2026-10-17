# SIPRE — Matriz de trazabilidad provisional

Fecha: 2026-10-16. **SRS y formulación ausentes**. TR-01…25 son referencias de cobertura de F8 creadas para este plan, NO IDs RF/RNF oficiales. Al recibir F2/F3, enlazar cada RF/RNF auténtico con estas filas, conservar referencias históricas y registrar discrepancias D01. Ninguna fila se declara implementada o probada.

Actualización F9 (2026-10-16): el usuario aportó la pauta completa de esta conversación: Innovación (30), Impacto social (20), Prefactibilidad/ambiente (20), Viabilidad técnica (20), suma 90. D23 queda resuelta respecto a su recepción; no se presuponen diez puntos adicionales. Los quince ítems se transcriben y vinculan a evidencia en [evaluation-rubric.md](evaluation-rubric.md). Abreviaturas de pauta: I, S, P, T respectivamente, sin asignar puntaje ganado.

Actualización H7 (2026-10-17): entregado el hito H7 (GIS, rutas y bloqueos) en `READY_FOR_REVIEW` sin declarar filas cerradas. Evidencia parcial: TR-03 (SRID 4326, medida métrica/geography, punto representativo de zona) y TR-12 (grafo dirigido con elegibilidad por vehículo, ida/vuelta con descarga, secuencia de arcos en `route_candidate_edges`, revisión optimista `expected_revision` e invalidación de candidatos al bloquear; BLOCKED/UNKNOWN no transitables; ausencia de ruta reportada como `ROUTE_NOT_FOUND` sin inventar modo aéreo) cubiertas por `backend/tests/unit/test_gis_routes.py` y `backend/tests/integration/test_gis_network.py` (51 pruebas verdes con BD real local y Docker, 17/17 checks Compose, ruff limpio). La migración `0006` corrige la cascada al invalidar rutas. Caducidad/STALE dependiente queda para H8; TR-09 permanece fuera de H7. Cierre formal pendiente de aprobación humana.

## Requisitos disponibles → componentes → hitos → pruebas → aceptación

| ID F8 | Requisito y fuente verificable | Componentes | Hitos | Pruebas | Criterio de aceptación / pauta |
|---|---|---|---|---|---|
| TR-01 | Respetar fuentes/trabajo previo y autorización; solicitud F8 §§3/5/7 | docs, Git, versiones | H1–H14 | auditoría de archivos/hashes y revisión por hito | Fuentes preservadas, cambios aprobados, sin avance automático; T |
| TR-02 | Registrar emergencias/reportes/necesidades con calidad; F6 §3/4/6 | emergencies, observations, domain, API | H2/H3/H9 | T8-DB-01, P4-T08/15, P5-T16/26 | FK/estados válidos, UNKNOWN distinto de cero, no mezcla de emergencias; S/T |
| TR-03 | Zonas/geometría/métrica espacial; F6 §5 | zones, gis, PostGIS | H2/H7 | T8-GEO-01 | SRID 4326, distancias métricas y punto representativo; T |
| TR-04 | Catálogo, bodegas, stock y reservas; F5 §3 R02; F6 §4 | resources, ledger, db | H2/H3/H8 | P5-T03/04/21, T8-CON-02 | Saldo libre conciliable y jamás negativo; S/T |
| TR-05 | Vehículos/unidades/cualificación/identidad; F5 R04–R11 | transport, resources, planning | H2/H6/H8 | P5-T05…15, F7-07…12 | Capacidad, compatibilidad, indivisibilidad y activo único; T |
| TR-06 | AHP geométrico/consistencia/perfil; F4 §5 | profiles, prioritization/ahp | H5 | P4-T01/02/03/16 | CR≤.10, RI8=1.41, w8 DEMO≤.08, sin perfil inválido; I/T |
| TR-07 | Ocho criterios y TOPSIS anclado; F4 §3/6/7 | prioritization | H5 | P4-T04/05/06/07/14 | Score y ranking fixture, anclaje y determinismo; I/T |
| TR-08 | Incertidumbre, faltantes, explicación; F4 §§4/9/11 | prioritization, observations, UI, analytics | H5/H9/H10 | P4-T08/09/10/12/13, F7-13/21 | Intervalos/flags/factores visibles; NULL no ocultado; I/S |
| TR-09 | Tiempo sin asistencia sin doble conteo; F4 C7/F5 §7 | observations, prioritization, metrics | H5/H6/H11 | P4-T11, P5-T27, F7-14 | C7 por hechos/tiempo; KPI privación fuera de H; I/S |
| TR-10 | MILP mixto y lexicografía; F5 §§4–6 | optimization, planning/evaluation | H6 | P5-T01/18/19/28 | H preservado y costo minimizado según estado demostrado; I/T |
| TR-11 | Déficit, demanda desconocida y estatus; F5 §§9/11 | planning, optimization, analytics | H6/H10 | P5-T03/16/17/20/23/24 | Todas zonas presentes, UNKNOWN≠0, timeout≠infeasible; S/T |
| TR-12 | Rutas legales/versionadas y horizonte; F5 §8/F6 §5 | gis, transport, optimization | H7/H6/H8 | P5-T10/11/12/21, T8-GEO-01/02 | BLOCKED/UNKNOWN nunca asignadas; cambios → STALE; T/S |
| TR-13 | Snapshot inmutable y reconstrucción; F6 §7 | db, application, jobs, profiles | H2/H3/H5/H6 | P4-T14/15, P5-T21/22/26, T8-SNAP-01 | Corrida usa una emergencia, datos/perfiles/hash inmutables; T |
| TR-14 | Decisión humana separada y reservas atómicas; F5 §10/F6 §6.3 | recommendations, auth, application | H4/H8/H9 | P4-T17, P5-T25, F7-23, T8-CON-01…03 | Sólo humano autorizado acepta; ninguna orden operacional automática; S/T |
| TR-15 | Auditoría y seguridad; F6 §9 | auth, audit, db, API | H4/H8/H12 | T8-AUTH-01/02, T8-AUD-01, T8-IDEM-01 | Actor de sesión, logs sin secretos, historia reconstruible; T |
| TR-16 | Portal operacional mínimo; F6 ADR-005 | UI Jinja2/HTMX, API | H9 | T8-UI-01 | Carga/revisión/decisión con permisos y contexto; sin segundo BI; T/S |
| TR-17 | Doce vistas y cinco dashboards; F6 §8 | analytics, Metabase | H10/H11/H14 | T8-BI-02, F7-22/25 | KPI conciliados, filtros/run/SIMULATED, NA e incertidumbre visibles; I/S/T |
| TR-18 | Metabase sólo lectura y DB separada; F6 ADR-003/004 | roles SQL, analytics, metabase_app | H1/H2/H10 | F7-26, T8-BI-01 | SELECT permitido sólo vistas; DML/DDL/tablas crudas denegadas; T |
| TR-19 | Stack local mantenible/reproducible; F6 §10–12 / pedido §G | Docker, locks, runbooks | H1/H12/H14 | T8-INF-01, T8-REC-01 | Arranque/restauración con versiones fijadas y recursos medidos; P/T |
| TR-20 | Trabajo asíncrono, resiliencia y observabilidad; F6 §10 | jobs, API, audit, db | H3/H12 | T8-JOB-01, T8-RES-01 | 202 durable, reintento idempotente, degradación explícita; T |
| TR-21 | 4×12=48 escenarios y 96 ejecuciones; F7 §§3/4 | generator, manifests, pipeline | H11/H13 | F7-02/03/04/20, T8-EXP-02 | Semillas 101…112 por familia, conteos/fallos completos; I/T |
| TR-22 | FIFO factible/justo y determinista; F7 §5 | baseline_fifo, planning | H11/H12/H13 | P5-T02, F7-01/05…12/15/18 | Cola temporal, mismos inputs/restricciones, no usa H para decidir; I/T |
| TR-23 | KPI/unidades/NA correctos; F7 §6 | metrics, evaluation, exports | H11/H14 | P5-T24/27, F7-14…18/25, T8-EXPORT-01 | Hnorm/cobertura crítica con denominadores correctos; no suma heterogénea; S/P |
| TR-24 | Congelamiento/aislamiento oracle; F7 §§4.1/7/8/11 | generator, pipeline, oracle aislado | H11/H12/H13 | F7-01/02/04/21/23, T8-EXP-01/02 | Mismo hash, sin oracle en algoritmos, sin ajuste post hoc; I/T |
| TR-25 | Exportación y análisis pareado transparentes; F7 §§9/10 | exports, analytics, docs | H13/H14 | F7-04/19/20/22/24/25/26 | 48 IDs aun con fallos, N por KPI, CSV/JSON/manifiesto conciliados; I/S/P/T |

## Matriz de restricciones duras

| F5 | Implementación y verificación | Pruebas fuente principales | Puerta |
|---|---|---|---|
| R01 | balances por demanda conocida / validator | P5-T16/23, F7-13 | H6/H11 |
| R02 | stock libre por depósito y recurso | P5-T03/04, F7-07 | H6/H8/H11 |
| R03 | vínculo x–y, combinación elegible | P5-T09, F7-06 | H6/H11 |
| R04 | una salida/destino y reserva global | P5-T15, F7-06/10 | H6/H8/H11 |
| R05 | capacidad peso | P5-T05, F7-08 | H6/H11 |
| R06 | capacidad volumen | P5-T06, F7-08 | H6/H11 |
| R07 | compatibilidad carga | P5-T09, F7-09 | H6/H11 |
| R08 | red/horizonte/disponibilidad | P5-T10/11/12, F7-11/12 | H7/H6/H11 |
| R09 | unidad única/cualificada/accesible | P5-T13/14, F7-09/10/12 | H6/H11 |
| R10 | balance especializado | P5-T13/23, F7-06/17 | H6/H11 |
| R11 | identidad física transversal | P5-T15, F7-10 | H6/H8/H11 |
| R12 | snapshot/legalidad/unidades | P5-T07/08/21/26, F7-01/04 | H2/H6/H8/H11 |
| R13 | NULL→verificación, no cantidad supuesta | P5-T16/17, F7-13/21 | H5/H6/H11 |

## Cobertura de pauta y límites

| Pauta citada | Evidencia futura | Limitación de la afirmación |
|---|---|---|
| Innovación 30 | AHP/TOPSIS explicable, MIP lexicográfico, E04 e integración reproducible; TR-06…12/21…24 | No afirmar novedad absoluta ni validación clínica |
| Impacto social 20 | Cobertura crítica, déficit por tipo/zona, desconocidos, decisión humana; TR-08/09/11/14/23 | KPI sintéticos no son vidas salvadas ni ensayo institucional |
| Prefactibilidad/ambiente 20 | Recursos/instalación medidos, km/utilización y costos declarados; TR-19/23/25 | Sin factores aprobados no convertir km en ahorro energético/emisiones |
| Viabilidad técnica 20 | 71 pruebas fuente + técnicas, snapshots, constraints, seguridad, demo/BI; TR-01…25 | Diseño no obtiene puntuación de pruebas aún inexistentes |
| Total de pauta recibida: 90 | D23 resuelta; quince ítems en evaluation-rubric.md | No inventar diez puntos adicionales ni normalizar a 100 |

## Cómo completar trazabilidad con el SRS

Registrar por requisito oficial: ID, texto aprobado y versión/hash, fila TR vinculada, componente/endpoint/tabla, hitos, prueba por ID, evidencia de ejecución y estado (pendiente/implementado/verificado/no aplicable con aprobación). Cubrir también RF/RNF que no aparezcan en F4–F7 y revisar impactos antes de programarlos. Si el SRS contradice un dominio ya aprobado, abrir decisión con dueño y alternativa; no corregir modelos automáticamente.

El catálogo íntegro P4-T01…17, P5-T01…28 y F7-01…26 está en [testing-strategy.md](testing-strategy.md). Cada caso técnico T8 también tiene hito y criterio allí. La cobertura de dominio sigue planificada. Las primeras verificaciones de infraestructura realizadas en F9, sin sustituir los 71 criterios fuente, están en [phase9-status.md](phase9-status.md).
