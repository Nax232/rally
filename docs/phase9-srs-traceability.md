# Fase 9 — Trazabilidad contra F2/F3

Fecha de actualización: 2026-10-17. Revisión de implementación tras ejecutar H1–H4 y H7 GIS; estado de cierre F9:
**READY_FOR_REVIEW** (pendiente de aprobación formal).

## Fuentes y criterio

Fuentes reales: [F2](../SIPRE_FORMULACION_v1.md), [F3](../SIPRE_SRS_v1.md), F4–F7 y sus JSON en la
raíz; no se presupone instalación desde ZIP. F2/F3 están completos y auditados, pero sus cierres
documentales solicitan ratificación del equipo. No se trasladaron ni editaron.

Alcance establecido: F6 §14 y [plan F8](implementation-plan.md), **Fase 9 ≈ H1–H4**. No confundir
con Hito 9 (interfaz operacional). Se conserva DoD existente, no se reduce a infraestructura.

Estados: IMPLEMENTED_AND_TESTED requiere evidencia ejecutada del criterio completo;
IMPLEMENTED_NOT_TESTED significa implementación observable con validación pertinente pendiente;
MISSING_IN_F9_SCOPE identifica una obligación actual ausente, incluso si tiene una parte posterior;
PLANNED_LATER es trabajo de otro hito; CONFLICT requiere decisión; NOT_APPLICABLE exige justificar
exclusión. No se usa PASS ni se excluye ningún requisito del SRS.

Evidencia común: [pruebas](phase9-test-evidence.md), [brechas G01–G09](phase9-gap-analysis.md).
El esquema completo, la API, el worker, la autenticación/RBAC y la auditoría persistente están
implementados y probados contra PostgreSQL/PostGIS real. Los motores matemáticos siguen
planificados para H5–H8.

## Objetivos F2

| Objetivo | Módulo/hito | Estado | Evidencia/límite |
|---|---|---|---|
| OE-01 Integración territorial | datos/GIS H2/H3/H7 | IMPLEMENTED_AND_TESTED (datos) | Entidades, procedencia y geometría 4326 en H2/H3; rutas H7 |
| OE-02 Caracterización | criterios H5 | PLANNED_LATER | F4 conservada |
| OE-03 Priorización | AHP/TOPSIS H5 | PLANNED_LATER | Sin motor |
| OE-04 Información incompleta | observaciones H2/H3; incertidumbre H5 | IMPLEMENTED_AND_TESTED (datos) | NULL vs cero y evidencia persistidos y probados; fórmula posterior |
| OE-05 Asignación | optimización H6/H7 | PLANNED_LATER | SCIP smoke no es modelo SIPRE |
| OE-06 Apoyo a decisión | H8 | PLANNED_LATER | No confundir 501 con flujo humano validado |
| OE-07 Visualización | Metabase H10 | PLANNED_LATER | Perfil Compose no es dashboard |
| OE-08 Validación | experimentos H11–H14 | PLANNED_LATER | 48 instancias/96 ejecuciones no realizadas |

## Los 103 requisitos del SRS

| ID | Requisito (texto del SRS) | Módulo / hito | Estado | Evidencia y alcance pendiente |
|---|---|---|---|---|
| RF-001 | Crear emergencia con nombre, tipo, fecha/hora, territorio, descripción y estado | emergencies · H2–H3 | IMPLEMENTED_AND_TESTED | Esquema, API idempotente y pruebas E2E/integración |
| RF-002 | Actualizar emergencia abierta | emergencies · H2–H3 | IMPLEMENTED_AND_TESTED | Revisión optimista `input_revision`, conflicto 409 |
| RF-003 | Cerrar emergencia manteniendo historial | emergencies · H2–H3 | IMPLEMENTED_AND_TESTED | Cierre sin edición ordinaria; historial conservado |
| RF-004 | Registrar zonas con `zone_id`, nombre, geometría, población basal y procedencia | zones · H2–H3 | IMPLEMENTED_AND_TESTED | Zonas MultiPolygon 4326 con fuente y corte |
| RF-005 | Asociar información espacial en puntos/polígonos según F6 | zones · H2–H3 | IMPLEMENTED_AND_TESTED | Geometría validada por PostGIS y por API |
| RF-006 | Asociar información basal a zona con fuente y corte temporal | zones · H2–H3 | IMPLEMENTED_AND_TESTED | `source_id`, `baseline_at`, calidad persistidos |
| RF-007 | Registrar reporte con zona, fenómeno/medida, unidad, fuente, `observed_at`, `recorded_at`, calidad y comentarios | reports · H2–H3 | IMPLEMENTED_AND_TESTED | Tabla e inserción con observaciones anidadas |
| RF-008 | Actualizar situación preservando historial de reportes | reports · H2–H3 | IMPLEMENTED_AND_TESTED | Historial append-only con inmutabilidad SQL |
| RF-009 | Calcular antigüedad de observación | reports · H2–H3 | IMPLEMENTED_AND_TESTED | `data_age_hours` calculado en lectura y probado |
| RF-010 | Registrar múltiples tipos de necesidades por zona | needs · H2–H3 | IMPLEMENTED_AND_TESTED | Varios tipos por zona; pruebas de FK y dominio |
| RF-011 | Registrar cantidad, unidad, urgencia, fuente, estado de evidencia y timestamp | needs · H2–H3 | IMPLEMENTED_AND_TESTED | Campos con validación y checks |
| RF-012 | Distinguir demanda confirmada, estimada aprobada y desconocida | needs · H2–H3 | IMPLEMENTED_AND_TESTED | Estados validados; aprobación exige `approve_estimate` |
| RF-013 | Catálogo de recursos con clase y unidad física | resources · H2–H3 | IMPLEMENTED_AND_TESTED | Catálogo con unidad e indivisibilidad |
| RF-014 | Inventario por bodega/depósito, con stock libre y reservado | inventory · H2–H3 | IMPLEMENTED_AND_TESTED | Saldos por depósito; reservas diferidas a H8 |
| RF-015 | Impedir asignación superior al stock | inventory · H2–H3 (asignación H6/H8) | IMPLEMENTED_AND_TESTED (invariante) | Invariante de saldo no negativo y no sobretiro concurrente; asignación completa en H6/H8 |
| RF-016 | Registrar vehículos y unidades con identidad física, clase, capacidad y estado | assets · H2–H3 | IMPLEMENTED_AND_TESTED | Activos con capacidad positiva e identidad única |
| RF-017 | Registrar disponibilidad/estado de vehículos | assets · H2–H3 | IMPLEMENTED_AND_TESTED | Estados con revisión de fila |
| RF-018 | Respetar capacidad de carga | gis/transport/optimization · H7/H6/H8 | PLANNED_LATER | Capacidades positivas e identidad de activos se exigen ya en RF-016; rutas y cargas calculadas se prueban en hitos posteriores. |
| RF-019 | Registrar condiciones y restricciones de arcos viales | gis · H7 | IMPLEMENTED_AND_TESTED | Arcos dirigidos, estados, clases permitidas, revisión y pruebas GIS unitarias/integradas |
| RF-020 | Excluir rutas bloqueadas | gis · H7; optimización H6 | IMPLEMENTED_AND_TESTED | Proveedor H7 no devuelve candidatos que crucen BLOCKED/UNKNOWN; uso por solver pendiente H6 |
| RF-021 | Actualizar bloqueo y provocar invalidación de propuestas antiguas | gis/planning · H7/H8 | PLANNED_LATER | H7 invalida candidatos y preserva auditoría, probado en Docker tras migración `0006`; marcado STALE de recomendaciones depende de H8 |
| RF-022 | Caracterizar C1 gravedad humana | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-023 | Caracterizar C2 población afectada | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-024 | Caracterizar C3 vulnerabilidad | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-025 | Caracterizar C4 infraestructura crítica | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-026 | Caracterizar C5 accesibilidad | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-027 | Caracterizar C6 servicios básicos | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-028 | Caracterizar C7 tiempo sin asistencia | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-029 | Caracterizar C8 incertidumbre | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-030 | Calcular tiempo desde asistencia efectiva por recurso/necesidad | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-031 | Representar privación temporal sin doble contabilización | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-032 | Asociar fuente y confianza/calidad a información operacional | observations · H2–H3 | IMPLEMENTED_AND_TESTED | Fuente obligatoria y calidad persistidas y probadas |
| RF-033 | Calcular índice de incertidumbre territorial | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-034 | No asignar prioridad cero por ausencia de reportes | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-035 | Administrar perfiles de pesos versionados | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-036 | Admitir matriz AHP de comparaciones pareadas | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-037 | Calcular consistencia AHP y bloquear publicación inconsistente | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-038 | Versionar matrices, pesos, criterios y parámetros | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-039 | Calcular puntuación TOPSIS anclada a referencias fijas | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-040 | Generar ranking estable por zona/emergencia/corte | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-041 | Generar etiqueta de prioridad operativa de demostración | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-042 | Explicar por qué una zona obtiene determinada puntuación | prioritization/profiles · H5 (GIS H7) | PLANNED_LATER | F4: 17 pruebas pendientes; para fuentes y NULL ver RF-032/RQD. No hay motor implementado. |
| RF-043 | Ejecutar cálculo de asignación autorizado sobre snapshot | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. Los snapshots de entrada ya existen. |
| RF-044 | Optimizar primero objetivo de cobertura humanitaria H | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-045 | Minimizar luego costo logístico preservando H | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-046 | Calcular déficit por recurso/zona | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-047 | Mostrar déficit sin ocultar escasez | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-048 | Asociar asignaciones a rutas factibles del escenario | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-049 | Respetar cargas, compatibilidades y unidades indivisibles | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-050 | Evitar vías bloqueadas o desconocidas | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-051 | Calcular distancia/costo logística y documentar su unidad | optimization · H6/H7/H10 | PLANNED_LATER | F5: 28 pruebas pendientes; smoke SCIP no verifica SIPRE. |
| RF-052 | Permitir a decisor autorizado proponer cambios en restricciones | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-053 | Solicitar nueva optimización tras cambios | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-054 | Registrar recomendaciones con estados propios | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-055 | Exigir acción humana explícita para aprobación | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-056 | Registrar decisión humana con actor, timestamp y resultado | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-057 | Registrar justificación ante modificación/rechazo | recommendations/decisions · H8 | PLANNED_LATER | Revalidación, reserva atómica y decisión humana se probarán en H8; auth básica pertenece a H4. |
| RF-058 | Registrar bitácora de eventos críticos | audit/snapshots/jobs · H2–H4 | IMPLEMENTED_AND_TESTED | Bitácora persistente e inmutable; actores reales verificados |
| RF-059 | Recuperar inputs, pesos, restricciones y resultados de corrida | snapshots/jobs · H2–H4 | IMPLEMENTED_AND_TESTED (inputs) | Snapshots inmutables con fingerprint y jobs verificados; pesos/restricciones/resultados en H5–H8 |
| RF-060 | Dashboard de situación general en Metabase OSS | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RF-061 | Dashboard de ranking y factores de prioridad | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RF-062 | Dashboard de recursos y logística | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RF-063 | Dashboard de indicadores principales | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RF-064 | Dashboard comparativo experimental | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RF-065 | Identificar alertas operacionales para revisión | analytics/Metabase · H10–H11; H8 | PLANNED_LATER | No hay tableros. Segregación BI sí verificada en H1/H2. |
| RNF-001 | Explicabilidad | explanations · H5/H6/H8 | PLANNED_LATER | Sin motores ni explicaciones. |
| RNF-002 | Trazabilidad | audit/snapshots · H2–H4 | IMPLEMENTED_AND_TESTED | Actor, revisión y eventos persistidos; correlación HTTP complementaria |
| RNF-003 | Reproducibilidad | snapshots · H2/H3; experiments H11–H14 | IMPLEMENTED_AND_TESTED (inputs) | Locks e inputs inmutables con fingerprint; semillas/confirmatorio posteriores |
| RNF-004 | Integridad | db/domain/API · H2/H3 | IMPLEMENTED_AND_TESTED | Entidades e invariantes de dominio probados por SQL directo y API |
| RNF-005 | Seguridad | auth · H4 | IMPLEMENTED_AND_TESTED | Sesiones, RBAC y autorización por emergencia probados |
| RNF-006 | Contraseñas | auth · H4 | IMPLEMENTED_AND_TESTED | Argon2id, sin fuga en respuestas ni auditoría |
| RNF-007 | Mínimo privilegio | auth/db/analytics · H2/H4/H10 | IMPLEMENTED_AND_TESTED | VIEWER implementado; privilegios mínimos por rol verificados |
| RNF-008 | Rendimiento | benchmarks · H12 | PLANNED_LATER | Sin SLA medido ni motores. |
| RNF-009 | Escalabilidad | db · H2; carga H12 | IMPLEMENTED_NOT_TESTED | Separación e índices presentes; carga 10/30/100 posterior |
| RNF-010 | Interoperabilidad | API · H3; export H14 | IMPLEMENTED_AND_TESTED (REST) | REST con contratos JSON/GeoJSON; export CSV en H14 |
| RNF-011 | Portabilidad | docker/config · H1 | IMPLEMENTED_AND_TESTED | Build y arranque validados en WSL/Docker (17/17) |
| RNF-012 | Persistencia | db/bootstrap/migrations · H1/H2 | IMPLEMENTED_AND_TESTED | Dos bases, roles, migración online, reinicio y restore verificados |
| RNF-013 | Georreferenciación | geo · H2 | IMPLEMENTED_AND_TESTED | PostGIS con SRID 4326, constraints y GiST probados |
| RNF-014 | Usabilidad | UI/Metabase · H9/H10 | PLANNED_LATER | No interfaz operacional ni evaluación de usuarios. |
| RNF-015 | Operación degradada | integration · H7/H12 | IMPLEMENTED_AND_TESTED (parcial) | 503 sin DB y 501 en motores verificados; no demuestra operación con datos precargados sin APIs externas. |
| RQD-001 | Fuente obligatoria para observaciones críticas | observations · H2/H3 | IMPLEMENTED_AND_TESTED | Fuente obligatoria en informes, necesidades y zonas |
| RQD-002 | `observed_at`, `recorded_at` y corte temporal | observations · H2/H3 | IMPLEMENTED_AND_TESTED | Tres tiempos con orden y corte verificados |
| RQD-003 | Observado vs estimado aprobado | observations · H2/H3 | IMPLEMENTED_AND_TESTED | Estados de evidencia con aprobación restringida |
| RQD-004 | Vigencia del dato | quality · H5 | PLANNED_LATER | Flags y umbrales F4 pendientes; almacenamiento temporal es RQD-002 |
| RQD-005 | Desconocido ≠ cero | observations · H2/H3 | IMPLEMENTED_AND_TESTED | `NULL` y `0` distinguidos y probados |
| RN-001 | Recomendación no equivale a decisión | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RN-002 | Ausencia de información no significa prioridad cero | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RN-003 | Ruta bloqueada/desconocida no se usa como transitable | gis H7; planning H6/H8 | IMPLEMENTED_AND_TESTED | Proveedor H7 excluye ambos estados y pruebas integradas lo verifican; integración con solver pendiente |
| RN-004 | No superar stock | planning · H5–H8 | IMPLEMENTED_AND_TESTED (invariante) | Invariante de stock verificado; regla de asignación completa en H6/H8 |
| RN-005 | No superar capacidad física/temporal del activo | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RN-006 | Déficit no negativo | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RN-007 | Objetivo humanitario precede a logístico | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RN-008 | Modificación humana relevante auditada | audit · H2–H4 | IMPLEMENTED_AND_TESTED | Eventos por actor con inmutabilidad; aplicación a motores y decisiones posterior |
| RN-009 | Corrida asociada a versión de parámetros | snapshots · H2–H4 | IMPLEMENTED_AND_TESTED (inputs) | Corridas ligadas a snapshot y fingerprint; versión de parámetros en H5–H8 |
| RN-010 | Estimaciones distinguidas de datos observados | observations · H2–H4 | IMPLEMENTED_AND_TESTED | Estado de evidencia distinto y probado |
| RN-011 | Emergencia cerrada no admite edición ordinaria | emergencies · H2–H4 | IMPLEMENTED_AND_TESTED | Bloqueo por trigger y por API, probados |
| RN-012 | Decisión requiere confirmación humana explícita | planning · H5–H8 | PLANNED_LATER | Regla de ejecución futura; RF-014/016 y RNF-004 cubren invariantes de datos iniciales. Ausencia de endpoints no prueba la regla. |
| RX-001 | Explicar prioridad | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |
| RX-002 | Explicar asignación | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |
| RX-003 | Explicar faltante | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |
| RX-004 | Explicar ruta | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |
| RX-005 | Explicar incertidumbre | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |
| RX-006 | Diferenciar recomendación y decisión | explanations · H5–H8 (RX-004 H7) | PLANNED_LATER | Salida explicable aún no implementada; validar con fixtures F4/F5 y flujo humano. |

## Criterios técnicos desagregados (no son nuevos requisitos SRS)

| Criterio | Relación | Estado | Evidencia |
|---|---|---|---|
| Health, 503 sin BD, correlación, redacción básica | RNF-011/012 | IMPLEMENTED_AND_TESTED | unit/test_infrastructure_api.py; conexión feliz simulada y real |
| Compatibilidad instalada y SCIP mixto mínimo | RNF-011 | IMPLEMENTED_AND_TESTED | pip check; test_dependency_smoke.py |
| Configuración Compose parseable y puertos locales | RNF-011 | IMPLEMENTED_AND_TESTED | config --quiet y test_delivery_invariants.py |
| Migración online, roles reales, persistencia | RNF-007/012 | IMPLEMENTED_AND_TESTED | 17/17 verificaciones Docker y 51 pruebas con BD real |
| Contrato único de error y listado de usuarios | RNF-005/010 | IMPLEMENTED_AND_TESTED | test_foundation_api.py; 401/403/422/503 |
| Modo operacional manual | F3 §4 vs F6 §4 | NOT_APPLICABLE | C01: usuario eligió explícitamente sólo SIMULATED para este prototipo; excepción SRS registrada, sin certificar registros reales |
| Estados de emergencia | F3 vs contrato F6 | IMPLEMENTED_AND_TESTED | C02: cuatro estados del SRS; estados de análisis/plan son entidades relacionadas, no estados de emergencia |
| Rol decisor | F3 DECIDER vs F6 DECISION_MAKER | IMPLEMENTED_AND_TESTED | C03: identificador técnico F6, capacidad explícita sin herencia de ADMIN; decisiones reales siguen en H8 |

No existe evidencia para declarar implementado y probado un requisito matemático o experimental
completo. Pauta: evidencia técnica parcial apoya PA-D1/D2; PA-D4 requiere aprobación formal
pendiente. Innovación, impacto social, eficiencia y usabilidad no se demuestran por tener
dependencias instaladas. Véase [pauta](evaluation-rubric.md); 15 ítems, 90 puntos, sin
autoasignación de nota.
