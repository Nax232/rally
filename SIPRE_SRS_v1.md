# SIPRE — Fase 3: Especificación de Requisitos de Software (SRS)

**Identificador:** SIPRE-F3 / SRS 1.0  
**Versión:** 1.0 — consolidación de la Fase 3 realizada en esta conversación, 2026-10-16.  
**Estado:** línea base académica preparada para revisión del equipo; **no certificada como validación de usuarios institucionales**.  
**Producto:** SIPRE — Sistema de Priorización y Optimización de Recursos en Post-Emergencia.  
**Documento rector de objetivos:** `SIPRE_FORMULACION_v1.md`.  
**Referencias de especialización:** `SIPRE_PRIORIZACION_v1.md` (F4), `SIPRE_OPTIMIZACION_v1.md` (F5), `SIPRE_ARQUITECTURA_v1.md` (F6), `SIPRE_EXPERIMENTOS_v1.md` (F7).

> **Base documental:** requisitos RF-001…RF-065, RNF-001…RNF-015, RQD-001…RQD-005, RN-001…RN-012 y RX-001…RX-006 establecidos en la Fase 3 del chat, ahora estructurados para su consumo por Codex. Los criterios de aceptación de tablas son **propuestas verificables de formalización**, no evidencias de pruebas ya ejecutadas. F4–F7 detallan las reglas exactas donde F3 dejaba parámetros abiertos.

## 1. Propósito, sistema y alcance

SIPRE es un prototipo académico SDSS cuyo fin es apoyar a decisores autorizados en la priorización de zonas y la recomendación de asignación de recursos post-desastre con restricciones de disponibilidad, capacidad, compatibilidad, acceso e incertidumbre. No emite órdenes de despacho ni sustituye estructuras oficiales de coordinación.

**MVP:** emergencia y zonas; reportes/observaciones; necesidad, inventario, flota, redes viales; ocho criterios; pesos AHP, ranking TOPSIS anclado, incertidumbre y privación; optimización lexicográfica con una salida/un destino por vehículo en el MVP; recomendaciones y déficits; intervención humana; auditoría; métricas y dashboards Metabase; escenarios comparativos FIFO_FEASIBLE/SIPRE.

**No incluidos:** monitoreo vial real, fuentes ALFA/FIBE en tiempo real, certificación institucional, despacho autónomo, seguimiento GPS en vivo, CVRP multiparada completo, predicción clínica individual, red descentralizada que funcione sin servidor/energía.

## 2. Actores y control de acceso

Los siguientes son **roles lógicos**, no equivalentes a atribuciones de un organismo real:

| Rol | Capacidades previstas | Restricciones |
|---|---|---|
| `ADMIN` Administrador | Configuración de entorno, gestión de usuarios, autorización de perfiles cuando proceda | No saltar trazabilidad ni emitir automáticamente decisiones |
| `OPERATOR` Operador | Registrar/importar emergencias, reportes, necesidades, stock y bloqueos según permisos | No aprobar despachos ni modificar perfiles aprobados |
| `ANALYST` Analista | Ver datos autorizados, ejecutar priorización y optimización, analizar resultados | No confirmar recomendaciones como autoridad |
| `DECIDER` Autoridad/decisor | Revisar, rechazar, proponer cambios, pedir recálculo y aprobar decisiones permitidas | No confirmar una propuesta obsoleta/inviable; toda acción auditada |
| `VIEWER` Observador | Consultar vistas y KPI autorizados | Nunca modificar datos, ejecutar operaciones privilegiadas ni aprobar |

El RBAC debe comprobarse **en API/servidor**, no sólo ocultando botones. Metabase tendrá su control de acceso propio y **cuenta SQL de solo lectura** sobre vistas agregadas `analytics`. No equivale a portal transaccional.

## 3. Casos de uso principales

| Caso | Actor primario | Flujo/respuesta |
|---|---|---|
| UC-01 Preparar emergencia | Operador | Crear emergencia y zonas; importar datos basales, red y fuentes |
| UC-02 Mantener situación | Operador | Registrar observaciones con calidad, necesidades y bloqueos; nueva revisión |
| UC-03 Preparar recursos | Operador | Registrar stock libre, depósitos, vehículos y unidades especializadas |
| UC-04 Calcular prioridad | Analista | Congelar snapshot, validar AHP, ejecutar F4, inspeccionar incertidumbre |
| UC-05 Generar plan | Analista | Ejecutar F5 sobre la misma versión, revisar entregas, faltantes y restricciones |
| UC-06 Revisar plan | Decisor | Revisar explicación, cambiar supuestos/restricciones, reoptimizar |
| UC-07 Confirmar o rechazar | Decisor | Verificar vigencia, registrar decisión y reservas de recursos; no despacho externo |
| UC-08 Consultar situación | Observador/analista | Dashboards Metabase de resultados autorizados y calidad de datos |
| UC-09 Simular y comparar | Analista | Ejecutar FIFO_FEASIBLE y SIPRE pareados en escenario sintético y registrar KPI |
| UC-10 Auditar corrida | Auditor/administrador autorizado | Recuperar snapshot, matrices, pesos, restricciones, resultados y decisiones |

### 3.1 Flujo principal y alternativas

1. Crear una emergencia `DRAFT` o un escenario `SIMULATED` claramente etiquetado.
2. Registrar zonas, reportes y necesidades con fuente y fecha de observación; conservar faltantes como NULL.
3. Registrar stock/vehículos, red y bloqueos con sus versiones.
4. Fijar el snapshot de inputs, perfiles y fecha de corte.
5. Ejecutar AHP/TOPSIS y guardar ranking, rango de sensibilidad y factores.
6. Ejecutar optimización con restricciones y ruta conocida de escenario; guardar faltantes y estados del solver.
7. Presentar `RECOMMENDATION`, pendiente de revisión.
8. Un decisor puede rechazar, requerir verificación o corregir supuestos y solicitar nueva corrida.
9. Antes de confirmar se verifican versiones de inventario, rutas y snapshot. Si alguna cambió, **rechazar confirmación por obsolescencia** y exigir nueva optimización.
10. Confirmación humana genera `DECISION` y reserva compatible en una transacción; no produce despacho externo.
11. Metabase visualiza resultados y auditoría agregada de sólo lectura.

**Alternativas obligatorias:** no hay recursos; hay rutas `BLOCKED` o `UNKNOWN`; demanda `NULL`; inventario insuficiente; solver `INFEASIBLE`/`TIME_LIMIT`/`ERROR`; permiso insuficiente; solicitud duplicada; cierre de emergencia; modificación concurrente.

## 4. Estados y terminología

**Emergencia:** `DRAFT`, `ACTIVE`, `CLOSED`, `CANCELLED` (los estados narrativos «en análisis/plan generado/validado» se implementan mediante corridas/planes relacionados, no requieren convertirse en nuevos estados obligatorios).  
**Escenario:** `SIMULATED` o `OPERATIONAL_RECORD` claramente indicado, siendo este último sólo un registro manual/no certificado en el MVP.  
**Observación:** `OBSERVED`, `ESTIMATED_APPROVED`, `UNKNOWN`, con control de fuente y timestamp; algunas interfaces podrán mostrar traducciones en español.  
**Red vial:** `VERIFIED_OPEN`, `VERIFIED_RESTRICTED`, `BLOCKED`, `UNKNOWN`, verificado sólo contra escenario/dataset.  
**Recomendación:** `GENERATED`, `UNDER_REVIEW`, `SUPERSEDED`, `REJECTED`, `ACCEPTED_AS_DECISION` (nombre técnico final según F6).  
**Decisión:** entidad separada de recomendación con actor, momento, justificación y compromisos de inventario.  
**Corrida de solver:** distinguir éxito, factible no óptima, sin solución factible, interrupción temporal y error técnico. Estados exactos según F5/F6.

## 5. Requisitos funcionales RF-001 a RF-065

Convención: **MUST** (necesario para el MVP, o su versión mínima), **SHOULD** (mejora razonable), **COULD** (futuro). La tabla incluye un criterio verificable básico por requisito, cuyo detalle se complementa con F4–F7. Ningún criterio indica que la prueba haya sido ejecutada.

### 5.1 Gestión de emergencias y territorio

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-001 | MUST | Crear emergencia con nombre, tipo, fecha/hora, territorio, descripción y estado | Un usuario autorizado obtiene ID único; faltan campos obligatorios → error sin crear registro |
| RF-002 | MUST | Actualizar emergencia abierta | Actor autorizado cambia atributos permitidos; se guarda auditoría y revisión |
| RF-003 | MUST | Cerrar emergencia manteniendo historial | `CLOSED` impide modificaciones operacionales sin reapertura autorizada; no se borran resultados |
| RF-004 | MUST | Registrar zonas con `zone_id`, nombre, geometría, población basal y procedencia | FK a emergencia, geometría válida y población no negativa; zonas importadas distinguidas de otras |
| RF-005 | MUST | Asociar información espacial en puntos/polígonos según F6 | Formato espacial coherente, SRID documentado y validación PostGIS |
| RF-006 | MUST | Asociar información basal a zona con fuente y corte temporal | Al menos fuente/calidad; no sustituye población afectada por población total automáticamente |

### 5.2 Reportes y observaciones

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-007 | MUST | Registrar reporte con zona, fenómeno/medida, unidad, fuente, `observed_at`, `recorded_at`, calidad y comentarios | Reporte válido persistido; reporte inválido rechazado sin perder anteriores |
| RF-008 | MUST | Actualizar situación preservando historial de reportes | El nuevo reporte no destruye el anterior; nueva revisión/snapshot al recalcular |
| RF-009 | MUST | Calcular antigüedad de observación | `data_age = as_of_time - observed_at`; fecha futura o inconsistente produce validación explícita |

### 5.3 Necesidades y demandas

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-010 | MUST | Registrar múltiples tipos de necesidades por zona | Se conserva `zone_id`, tipo y clase/unidad de demanda |
| RF-011 | MUST | Registrar cantidad, unidad, urgencia, fuente, estado de evidencia y timestamp | Cantidad conocida no negativa; nulos y desconocidos distinguidos |
| RF-012 | MUST | Distinguir demanda confirmada, estimada aprobada y desconocida | `UNKNOWN` mantiene NULL; optimizador no asigna un valor supuesto |

### 5.4 Inventario, recursos y flota

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-013 | MUST | Catálogo de recursos con clase y unidad física | Agua litros, kits unidades, etc.; conversiones documentadas |
| RF-014 | MUST | Inventario por bodega/depósito, con stock libre y reservado | Saldo disponible no negativo; reserva confirmada afecta stock libre una sola vez |
| RF-015 | MUST | Impedir asignación superior al stock | Rechaza recomendación o confirmación que supera stock libre; test por depósito/recurso |
| RF-016 | MUST | Registrar vehículos y unidades con identidad física, clase, capacidad y estado | Capacidades positivas; `physical_asset_id` evita dobles activaciones |
| RF-017 | MUST | Registrar disponibilidad/estado de vehículos | Sólo vehículos disponibles son candidatos; cambios versionan inventario/activos |
| RF-018 | MUST | Respetar capacidad de carga | Peso y volumen máximos; no se acepta vehículo sobrecargado |

### 5.5 Accesibilidad y red vial

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-019 | MUST | Registrar condiciones y restricciones de arcos viales | Estados `VERIFIED_OPEN`, `VERIFIED_RESTRICTED`, `BLOCKED`, `UNKNOWN`; revisión/versionado |
| RF-020 | MUST | Excluir rutas bloqueadas | Un arco `BLOCKED` no aparece en ninguna ruta confirmable |
| RF-021 | MUST | Actualizar bloqueo y provocar invalidación de propuestas antiguas | Cambiar `road_revision` hace fallar aprobación de propuesta obsoleta |

### 5.6 Ocho dimensiones de criticidad (F4)

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-022 | MUST | Caracterizar C1 gravedad humana | Cálculo/estado según normalización F4, no triaje individual |
| RF-023 | MUST | Caracterizar C2 población afectada | No usar población total como número de afectados sin dato respaldo |
| RF-024 | MUST | Caracterizar C3 vulnerabilidad | Conteos agregados sin duplicación de personas, valores justificados |
| RF-025 | MUST | Caracterizar C4 infraestructura crítica | Severidad/interrupción y cobertura territorial según F4 |
| RF-026 | MUST | Caracterizar C5 accesibilidad | Sin ruta verificada ≠ ruta abierta; ausencia de datos ≠ aislamiento confirmado |
| RF-027 | MUST | Caracterizar C6 servicios básicos | Agua, energía, saneamiento y telecomunicaciones según perfil versionado |
| RF-028 | MUST | Caracterizar C7 tiempo sin asistencia | Sólo necesidades efectivas/confirmadas; suministros parciales no reinician toda necesidad |
| RF-029 | MUST | Caracterizar C8 incertidumbre | Agregar completitud, antigüedad y conflicto; presentar separadamente de daño confirmado |
| RF-030 | MUST | Calcular tiempo desde asistencia efectiva por recurso/necesidad | Determinismo respecto a `as_of_time`; nunca usar reloj cambiante dentro de misma corrida |
| RF-031 | MUST | Representar privación temporal sin doble contabilización | F4 define C7; F5 registra KPI sin volver a multiplicar H arbitrariamente por tiempo |

### 5.7 Calidad e incertidumbre

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-032 | MUST | Asociar fuente y confianza/calidad a información operacional | Evidencia conservada; umbrales de demo identificados como tales |
| RF-033 | MUST | Calcular índice de incertidumbre territorial | Aplicar fórmula F4; muestra valor y banderas de verificación |
| RF-034 | MUST | No asignar prioridad cero por ausencia de reportes | Valores faltantes conservados como NULL y límites; `needs_verification` cuando corresponde |

### 5.8 AHP y TOPSIS

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-035 | MUST | Administrar perfiles de pesos versionados | Suma 1 y pesos positivos; versión usada se asocia a cada corrida |
| RF-036 | MUST | Admitir matriz AHP de comparaciones pareadas | Matriz 8×8, positiva, diagonal 1, reciprocidad y estructura válida |
| RF-037 | MUST | Calcular consistencia AHP y bloquear publicación inconsistente | CI/CR según F4; CR >0.10 impide aprobación de nuevo perfil demo |
| RF-038 | MUST | Versionar matrices, pesos, criterios y parámetros | Reejecutar con el perfil guardado; no editar perfil ya usado |
| RF-039 | MUST | Calcular puntuación TOPSIS anclada a referencias fijas | Puntaje [0,1], determinista, igual a ejemplos numéricos de F4 |
| RF-040 | MUST | Generar ranking estable por zona/emergencia/corte | Puntaje descendente; desempate `zone_id` según F4 |
| RF-041 | MUST | Generar etiqueta de prioridad operativa de demostración | Bandas de F4; visibilidad de incertidumbre y evidencia adicional |
| RF-042 | MUST | Explicar por qué una zona obtiene determinada puntuación | Exponer criterios, pesos, distancias TOPSIS, límites y banderas, sin atribuir falsamente contribuciones aditivas exactas |

### 5.9 Optimización humanitaria y logística

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-043 | MUST | Ejecutar cálculo de asignación autorizado sobre snapshot | Retorna `optimization_run_id` y estados por etapa; conserva entradas/versiones |
| RF-044 | MUST | Optimizar primero objetivo de cobertura humanitaria H | Solución satisface demandas conocidas, stock, rutas y restricciones F5 |
| RF-045 | MUST | Minimizar luego costo logístico preservando H | Segunda etapa satisface `H >= H* - epsilon_H`; no colapsa objetivos con H − λkm |
| RF-046 | MUST | Calcular déficit por recurso/zona | Demanda conocida − entrega = faltante ≥0; desconocido marcado como UNKNOWN |
| RF-047 | MUST | Mostrar déficit sin ocultar escasez | Metabase/API refleja faltantes conocidos y estado de no cobertura |
| RF-048 | MUST | Asociar asignaciones a rutas factibles del escenario | Ruta de un destino/salida desde origen y regreso si perfil requiere, no CVRP completo |
| RF-049 | MUST | Respetar cargas, compatibilidades y unidades indivisibles | No fraccionar kits/ambulancias ni exceder masa/volumen/activos |
| RF-050 | MUST | Evitar vías bloqueadas o desconocidas | Ruta `BLOCKED/UNKNOWN` excluida de resultados confirmables |
| RF-051 | MUST | Calcular distancia/costo logística y documentar su unidad | Distancia (km) y/o tiempo respaldado por red versionada; nunca usar distancia en línea recta como prueba de transitabilidad |

### 5.10 Intervención humana, recomendaciones y auditoría

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-052 | MUST | Permitir a decisor autorizado proponer cambios en restricciones | Cambio auditado, con fuente y justificación; no altera snapshot antiguo |
| RF-053 | MUST | Solicitar nueva optimización tras cambios | Nueva corrida/recomendación con versión actual; anterior no sobrescrita |
| RF-054 | MUST | Registrar recomendaciones con estados propios | Son distintas de decisiones; no reservan stock por generarse |
| RF-055 | MUST | Exigir acción humana explícita para aprobación | Motor/API no generan decisión por defecto; pruebas de permisos y rechazo automático |
| RF-056 | MUST | Registrar decisión humana con actor, timestamp y resultado | Verifica revisiones antes de confirmar y reserva recursos atómicamente (F6) |
| RF-057 | MUST | Registrar justificación ante modificación/rechazo | Nota y causal trazables a propuesta/versiones previas |
| RF-058 | MUST | Registrar bitácora de eventos críticos | Log lógico de sólo anexado (sin pretender garantía criptográfica por defecto) |
| RF-059 | MUST | Recuperar inputs, pesos, restricciones y resultados de corrida | Snapshot/artefactos identificados por revisión/hashes cuando corresponda |

### 5.11 Metabase y alertas

| ID | Prioridad | Requisito funcional | Verificación / aceptación mínima |
|---|---|---|---|
| RF-060 | MUST | Dashboard de situación general en Metabase OSS | Prioridad global, zonas, reportes, poblaciones, timestamps, filtro por emergencia |
| RF-061 | MUST | Dashboard de ranking y factores de prioridad | Score, bandera de incertidumbre, evolución y pesos versionados |
| RF-062 | MUST | Dashboard de recursos y logística | Inventario, recomendaciones, déficit, flota, rutas, revisión |
| RF-063 | MUST | Dashboard de indicadores principales | Cobertura, faltantes, utilización, distancia, etiquetas `SIMULATED` |
| RF-064 | MUST | Dashboard comparativo experimental | FIFO_FEASIBLE vs SIPRE sobre la misma instancia/semilla y KPI |
| RF-065 | SHOULD | Identificar alertas operacionales para revisión | Críticos sin asignación, datos viejos, stock insuficiente, ruta bloqueada e incertidumbre alta; **alertas informativas, no despachos** |

**Ampliación de F6:** además del mínimo de F3, la arquitectura contempla dashboard de seguimiento de decisiones. Puede organizarse como un tablero adicional o incluirse en el dashboard logístico. Evitar duplicación innecesaria.

## 6. Requisitos no funcionales RNF-001 a RNF-015

| ID | Necesidad | Criterio verificable |
|---|---|---|
| RNF-001 | Explicabilidad | Cada prioridad relevante registra entrada, método, pesos, incertidumbre y salidas; cada plan registra faltantes/estado y restricciones |
| RNF-002 | Trazabilidad | Cada corrida tiene ID, tiempo, actor y versiones de snapshot/modelo; modificaciones auditadas |
| RNF-003 | Reproducibilidad | Inputs y parámetros inmutables, semillas guardadas; tolerancias numéricas según F4–F7 |
| RNF-004 | Integridad | Validaciones API/BD: no negativos, unidades coherentes, FKs, no NaN/Inf, consistencia espacial |
| RNF-005 | Seguridad | Autenticación y RBAC aplicados en backend; nunca confiar sólo en interfaz |
| RNF-006 | Contraseñas | Hash seguro y secretos fuera del repositorio; no guardar contraseñas planas |
| RNF-007 | Mínimo privilegio | VIEWER sin escrituras; Metabase con rol SQL SELECT sólo sobre `analytics` |
| RNF-008 | Rendimiento | Resultados en tiempo interactivo del MVP; reportar benchmarks sin afirmar SLA sin medición |
| RNF-009 | Escalabilidad | Capas modulares, índices espaciales/datos; pruebas de carga de escenario 10/30/100 zonas |
| RNF-010 | Interoperabilidad | JSON, CSV, GeoJSON y REST donde resulte aplicable, con contratos versionados |
| RNF-011 | Portabilidad | Docker Compose, configuración reproducible, instalación local documentada |
| RNF-012 | Persistencia | PostgreSQL/PostGIS, migraciones y volúmenes; base separada para metadatos de Metabase |
| RNF-013 | Georreferenciación | SRID/CRS definido, geometrías válidas, distancia/métrica con unidades y procedencia |
| RNF-014 | Usabilidad | Operador no debe conocer matemática para entender ranking/recomendación; etiquetas claras y estado visible |
| RNF-015 | Operación degradada | Falta de APIs externas no inutiliza necesariamente SIPRE si API, DB, red local y datos precargados siguen disponibles; no equivale a operación desconectada total |

## 7. Calidad de datos RQD-001 a RQD-005

| ID | Regla | Verificación |
|---|---|---|
| RQD-001 | Fuente obligatoria para observaciones críticas | Registro sin fuente/documentación de origen rechazado o marcado no utilizable |
| RQD-002 | `observed_at`, `recorded_at` y corte temporal | Cálculos distinguen hora observada de registro; datos futuros inválidos salvo política explícita |
| RQD-003 | Observado vs estimado aprobado | Calidad no se pierde al agregar/sumar observaciones; estimaciones no se presentan como constataciones |
| RQD-004 | Vigencia del dato | Flags de dato viejo según perfil/umbral documentado; disparan revisión |
| RQD-005 | Desconocido ≠ cero | NULL conserva estatus UNKNOWN; no generar falsa seguridad ni despacho por demanda inventada |

## 8. Reglas de negocio RN-001 a RN-012

| ID | Regla obligatoria | Resultado ante incumplimiento |
|---|---|---|
| RN-001 | Recomendación no equivale a decisión | No crear orden/reserva al recomendar |
| RN-002 | Ausencia de información no significa prioridad cero | Activar tratamiento de faltantes de F4 |
| RN-003 | Ruta bloqueada/desconocida no se usa como transitable | Excluir candidato o marcar no confirmable |
| RN-004 | No superar stock | Rechazar asignación/confirmación inválida |
| RN-005 | No superar capacidad física/temporal del activo | Rechazar ruta/carga inválida |
| RN-006 | Déficit no negativo | Rechazar dato inconsistente o corregir modelo de balance |
| RN-007 | Objetivo humanitario precede a logístico | Mantener lexicografía con H protegida |
| RN-008 | Modificación humana relevante auditada | Guardar actor, justificación, fecha y revisión |
| RN-009 | Corrida asociada a versión de parámetros | Invalidar cálculo no reproducible |
| RN-010 | Estimaciones distinguidas de datos observados | Etiquetar/autorizar uso según perfil y evidencia |
| RN-011 | Emergencia cerrada no admite edición ordinaria | Exigir reapertura auditada, si se habilita |
| RN-012 | Decisión requiere confirmación humana explícita | No aprobar planes automáticamente |

## 9. Requisitos de explicabilidad RX-001 a RX-006

| ID | Necesidad | Salida comprobable |
|---|---|---|
| RX-001 | Explicar prioridad | Lista C1–C8, estado, pesos, score, rangos, TOPSIS y alertas de verificación |
| RX-002 | Explicar asignación | Necesidades, prioridad, recursos compatibles, restricciones y resultado de H |
| RX-003 | Explicar faltante | Demanda conocida, asignación posible, motivo stock/capacidad/ruta y estado |
| RX-004 | Explicar ruta | Red/versiones, origen, destino, arcos, bloqueos y km, sin atribuir verificación de campo inexistente |
| RX-005 | Explicar incertidumbre | Dato faltante/antiguo/contradictorio, intervalo de sensibilidad, efecto potencial |
| RX-006 | Diferenciar recomendación y decisión | IDs y estados diferentes; decisión asociada a aprobación y auditoría |

## 10. Contratos mínimos de datos

### 10.1 Entrada observacional

`emergency_id`, `zone_id`, `metric_code`, `value_numeric` nullable, `unit`, `source_id`, `observed_at`, `recorded_at`, `evidence_status`, `quality_flags`. El estado de evidencia exige que `UNKNOWN` conserve `value_numeric = null`.

### 10.2 Resultado de priorización

`priority_run_id`, `emergency_id`, `zone_id`, `as_of_time`, `score_estimate`, `score_lower`, `score_upper`, `rank`, `priority_level_demo`, `uncertainty_index`, `needs_verification`, `missing_criteria`, `factor_details`, `ahp_profile_version`, `criteria_profile_version`. Definiciones exactas en F4.

### 10.3 Resultado de optimización

`optimization_run_id`, `priority_run_id`, `input_snapshot_id`, `stage1_status`, `stage2_status`, `objective_h`, `objective_logistic`, `assignments`, `unmet_needs`, `routes`, `constraints_summary`, `solver_status`, `verification_flags`, `generated_at`. Definiciones exactas en F5.

### 10.4 Decisión humana

`decision_id`, `recommendation_id`, `actor_id`, `action`, `decision_at`, `reason`, `input_revision`, `inventory_revision`, `road_revision`, `reservations`; transacción de aceptación con detección de obsolescencia y doble reserva según F6.

### 10.5 Resultados experimentales

Contrato y nombres de columnas en `SIPRE_RESULTADOS_SCHEMA_v1.json`; las 4 familias, 12 semillas cada una, 48 instancias/96 ejecuciones pareadas y pruebas F7 corresponden a `SIPRE_EXPERIMENTOS_v1.md`.

**Regla:** los campos anteriores son mínimos semánticos del SRS; para esquemas, tablas, rutas HTTP y estados exactos consultar los contratos F6/F7, registrando incompatibilidades como issue y sin renombrarlos arbitrariamente.

## 11. Excepciones, errores y pruebas negativas

| Condición | Comportamiento esperado |
|---|---|
| Sin recursos | Resultado factible de asignación vacía con déficit conocido; jamás crash u orden de despacho inexistente |
| Zona sin ruta habilitada | No inventar camino, excluir del despacho factible y mostrar necesidad pendiente |
| Demanda desconocida | Conservar NULL, marcar verificación, no convertir en cero ni recomendar cantidad asumida |
| AHP inconsistente | No activar perfil nuevo y comunicar `INVALID_AHP_PROFILE` |
| Stock negativo/unidades incompatibles | Validación 4xx / constraint DB y sin mutación parcial |
| Error del solver | Estado diferenciado `INFEASIBLE`, `TIME_LIMIT` o `ERROR` según causa, conservar información diagnóstica |
| Ruta bloqueada después del cálculo | Cambiar `road_revision`, invalidar aprobación previa y exigir recálculo |
| Cambio de stock durante confirmación | Rechazar/serializar transacción, sin doble reserva; `STALE_REQUIRES_REOPTIMIZATION` |
| Usuario VIEWER intenta aprobar | HTTP 403 y evento auditado según política |
| Metabase intenta escribir en BD operacional | Cuenta limitada a SELECT: operación denegada |
| Dashboard muestra escenario sintético | Etiqueta `SIMULATED` visible, sin confundirse con reporte real |

## 12. MoSCoW y estrategia MVP

**MUST:** RF-001…RF-064 con su alcance mínimo, reglas RN/RQD/RX y RNF de integridad, seguridad y trazabilidad. Los RF de rutas se refieren a un destino por salida, NO CVRP completo. Las funciones visuales se resuelven con Metabase OSS y vistas SQL; aprobación se hace fuera de Metabase.

**SHOULD:** RF-065, importación CSV/GeoJSON más cómoda, análisis exploratorio de sensibilidad, UX mejorada, alertas visuales no autónomas y apoyo adicional a la revisión de calidad.

**COULD:** exportación PDF, informes automáticos, mapa avanzado multipolígono, integraciones externas públicas no esenciales.

**WON'T (MVP):** IA generativa embebida, drones/IoT, predicción clínica o de fenómenos, app ciudadana, integración oficial en tiempo real, órdenes automáticas de despacho, CVRP multiparada completo y garantía de operación sin energía/conectividad local.

**Nota de planificación:** el orden de implementación y posibles hitos diferidos se acuerdan con el equipo mediante Fase 8; no declarar Fase 9 fallida por carecer de dashboards de fases posteriores. Evaluar «Definition of Done» del hito presente, no el MVP completo.

## 13. Matriz de trazabilidad principal

| Grupo | Requisitos | Módulo F6 | Pruebas/escenarios | Pauta |
|---|---|---|---|---|
| Emergencia y territorio | RF-001…RF-006 | `emergencies`, `zones`, `geo` | CRUD, FKs, Geo, permisos | Viabilidad |
| Observaciones y calidad | RF-007…RF-012, RQD | `observations`, `resources` | NULL vs 0, fuentes, E04 | Innovación/impacto |
| Inventario/flota | RF-013…RF-018 | `resources`, `transport` | Stock/capacidad, F5 | Optimización |
| Accesibilidad | RF-019…RF-021, RN-003 | `transport`, `geo` | E03, invalidación de ruta | Viabilidad |
| Criterios | RF-022…RF-034 | `prioritization` | F4, E04 | Innovación/impacto |
| AHP/TOPSIS | RF-035…RF-042, RX-001 | `profiles`, `prioritization` | 17 pruebas F4 | Innovación/viabilidad |
| Optimización | RF-043…RF-051, RN-004…007 | `optimization` | 28 pruebas F5 | Impacto/eficiencia |
| HITL y auditoría | RF-052…RF-059, RX-006 | `recommendations`, `audit` | Auth, concurrencia | Ética/usabilidad |
| BI/alertas | RF-060…RF-065 | `analytics`, Metabase | SELECT-only, datos demo | Usabilidad |
| Experimentos | UC-09, métricas, RNF-003 | `experiments` | 26 pruebas F7, E01–E04 | Viabilidad/impacto |

## 14. Criterios de aceptación del SRS y control de cambios

**Una implementación cumple el SRS para su hito** si demuestra mediante tests/logs: requisitos aplicables implementados, datos válidos, autorización y estado consistentes, errores no destructivos, documentación y trazabilidad de entradas/salidas; los pendientes de otros hitos quedan identificados como `NOT_IMPLEMENTED` o `DEFERRED`, no como `PASS`.

**Cambios:** cualquier decisión que modifique objetivo, fórmula matemática, interpretación de evidencia, seguridad, jerarquía humanitaria, tratamiento de rutas, permisos de Metabase o protocolo experimental requiere registrar issue/ADR con:
`id`, especificaciones afectadas, conflicto, propuesta, evidencia, riesgos, decisión humana y versión resultante. Codex no debe corregir silenciosamente.

**Precedencia de especificaciones:** F2 define propósito y alcance; F3 define capacidades exigidas; F4 define matemáticas exactas de priorización; F5 las de optimización/ruteo MVP; F6 diseña implementación técnica y contratos; F7 congela experimento. Si hay una contradicción genuina, elevarla antes de afectar código. Los refinamientos de F4–F7 aclaran F3, pero no autorizan a eliminar requisitos funcionales sin aprobación.

## 15. Riesgos y decisiones aún abiertas

- Validación por usuarios reales y atribuciones institucionales: **pendiente**.
- Pesos, subpesos, umbrales y referencias reales: **pendiente** (los valores del prototipo son DEMO).
- Requisitos cuantitativos definitivos de tiempo, disponibilidad y recuperación: **pendientes de medición y presupuesto**, no afirmar SLA.
- Diseño definitivo de portal operacional ligero (Jinja2/HTMX propuesto en F6): **pendiente de ratificación**.
- Capacidad cartográfica específica de Metabase OSS en la versión instalada: **debe comprobarse**.
- Respuesta con conectividad ausente: sólo modo degradado con servidor/BD/red local disponibles en MVP.
- Requisitos regulatorios, gestión de información sensible y responsabilidades institucionales para un sistema real: fuera de acreditación de este MVP académico.

**Cierre documental:** SRS consolidado para que Codex compare implementación e identifique diferencias. Requiere revisión del equipo antes de declararse formalmente «aprobado» y no supone validación operacional de instituciones públicas.
