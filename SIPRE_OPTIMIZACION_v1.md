# SIPRE — Fase 5: Modelo de optimización humanitaria y logística

**Versión:** 1.0 / especificación de diseño para un prototipo académico.  
**Estado:** Diseño matemático cerrado para la variante MVP, pendiente de implementación, pruebas automáticas y validación con especialistas.  
**Proyecto:** Sistema de Priorización y Optimización de Recursos en Post-Emergencia.  
**Dependencias:** `SIPRE_PRIORIZACION_v1.md` (Fase 4), formulación de Fase 2 y requisitos RF/RNF de Fase 3.  
**Tecnologías previstas:** Python, Google OR-Tools (MIP), FastAPI, PostgreSQL/PostGIS, Metabase; Codex será el agente de desarrollo posterior.  
**Ámbito:** planificación de despachos *recomendados* durante las primeras 72 h de una post-emergencia simulada. No dirige operaciones reales ni reemplaza criterio profesional/COGRID.

## 0. Objetivo, límites y decisiones irrevocables de diseño

SIPRE recibe las prioridades territoriales calculadas en Fase 4 y recomienda **asignaciones físicamente posibles** de recursos. El sistema distingue entre: (A) **bienes transportables** como agua y kits, (B) **unidades especializadas indivisibles** como ambulancia equipada, equipo de rescate o equipo de maquinaria (con personal y capacidad declarados), y (C) **vehículos de transporte** usados para mover los bienes. Una unidad especializada no se modela simplemente como “litros de recurso”; una ambulancia con dotación se representa como unidad indivisible y requiere compatibilidad de misión.

**Jerarquía lexicográfica obligatoria:** primera etapa, maximizar cobertura humanitaria ponderada `H`; segunda etapa, **sin deteriorar significativamente la cobertura de la primera**, minimizar distancia/costo logístico de una solución factible. No crear una suma simple `H - λ·km` como objetivo primario; ello permitiría compensar una necesidad crítica con kilómetros.

**MVP robusto:** una salida/recorrido (sortie) por vehículo disponible y **un destino por salida**, con ruta verificada y retorno a base si el escenario exige retorno. Esta es una **asignación y distribución capacitada de un destino por vehículo**, NO un CVRP completo. La extensión de rutas **CVRP multi-parada** se considera un módulo avanzado posterior que requiere verificar conjuntamente factibilidad de cantidades, carga, ventanas de tiempo, rutas y cobertura; jamás llamar “CVRP implementado” a un itinerario de un único destino. La regla MVP responde a la necesidad de asegurar que **una buena solución de asignación tenga rutas realmente factibles**. Las salidas con múltiples paradas sólo se permitirán si se integran las restricciones de ruteo y existe verificación completa antes de recomendar el plan.

**Human-in-the-loop:** la salida del solver es `RECOMMENDATION`, no `CONFIRMED_DECISION` ni `DISPATCH_ORDER`. Se requiere aprobación humana, versión de inventario y verificación de vigencia vial al confirmar.

## 1. Contrato entre Fase 4 y Fase 5

Entradas obligatorias del motor de Fase 4 por zona `i`: `priority_score ∈ [0,1]`, `priority_rank`, `priority_run_id`, `criteria_profile_version`, `score_lower/upper`, `uncertainty_index`, `needs_verification`, `as_of_time`. Exigir que las zonas compartan una misma emergencia y snapshot de priorización. **TOPSIS es un indicador de urgencia relativa, no una demanda de recursos, probabilidad de muerte ni valor monetario.**

Entradas adicionales de la fase 5: demanda por zona y clase de recurso (incluida procedencia/calidad), stock por depósito, flota de transporte y vehículos especializados, depósitos, capacidades, base de cada unidad, compatibilidades, disponibilidad, grafo vial y estado/verificación de rutas, ventana de planificación y perfil de parámetros humanitarios/logísticos.

Salidas: `optimization_run_id`, `priority_run_id`, `status_stage1`, `status_stage2`, valor de objetivo humanitario, objetivo logístico (con unidad), asignaciones por zona/tipo/depot/vehículo, unidades desplegables, rutas con trayecto y estado, faltantes por demanda, problemas de cobertura, necesidades de verificación, auditoría y recomendación pendiente de aprobación.

## 2. Conjuntos, índices y unidades

- `I`: zonas de la emergencia; `i ∈ I`.
- `D`: depósitos/bodegas de origen; `d ∈ D`.
- `V`: vehículos de transporte para cargas; `v ∈ V`. `o(v) ∈ D` es su depósito de salida.
- `R`: recursos físicos transportables; `r ∈ R` (agua en litros, kits en unidades, etc.).
- `K`: tipos de necesidad de unidad especializada indivisible; `k ∈ K` (ambulancia con equipo, rescatistas en unidad organizada, maquinaria con operador, etc.).
- `U`: unidades especializadas desplegables; `u ∈ U`; cada unidad tiene ubicación y cualificaciones.
- `E_v ⊆ I`: zonas con ruta **verificada y autorizada** para vehículo `v`.
- `E_u ⊆ I`: zonas con ruta **verificada y autorizada** para unidad `u`.

No usar una variable única que sume litros, medicamentos, vehículos y personas como si fueran magnitudes equivalentes. Cada recurso tiene **unidad nativa**, y para carga se declaran coeficientes físicos por unidad (`kg/unit`, `m³/unit`).

## 3. Parámetros

### 3.1 Demanda, dotaciones e inventario

- `p_i`: `priority_score` de Fase 4 para zona `i` (adimensional, fijo en una corrida).
- `q_ir ≥ 0`: demanda aún no atendida y **autorizada para planificación** del recurso `r` en la zona `i`, en su unidad nativa. `q_ir=NULL` se trata como **desconocido** y NO equivale a 0.
- `n_ik ∈ Z≥0`: demanda aún no cubierta de unidades completas del tipo especializado `k` para la zona `i`.
- `s_dr ≥ 0`: stock libre real del recurso `r` en depósito `d`, descontando reservas/compromisos ya confirmados.
- `m_r ≥0`: peso en kg por unidad del recurso `r`; `b_r ≥0`: volumen en m³ por unidad.
- `W_v,B_v>0`: carga máxima por peso y volumen del vehículo `v`.
- `available_v`, `available_u`: disponibilidad documentada de vehículo o unidad.
- `compatible_vr`, `qualified_uk`: compatibilidad (vehículo/carga) y cualificación (unidad/servicio), respectivamente.
- `physical_asset_id`: clave para evitar utilización simultánea de un mismo activo cuando aparezca representado en dos inventarios.

### 3.2 Accesibilidad, horizonte y costos

- `L_vi`: longitud total documentada de la ruta (km) desde el depósito de `v` a `i`, incluyendo regreso si el perfil exige retorno.
- `T_vi`: tiempo total estimado de salida, viaje, descarga y eventual regreso (h).
- `L_ui`, `T_ui`: equivalentes para unidades especializadas `u` (según su base).
- `H`: horizonte operativo de la corrida (h), explícito y positivo. No confundir con las 72 h de alcance general del sistema; cada corrida puede planificar, por ejemplo, una ventana de 6 h.
- `route_status ∈ {VERIFIED_OPEN, VERIFIED_RESTRICTED, BLOCKED, UNKNOWN}`; UNKNOWN nunca se presupone abierto.
- `c_vi`, `c_ui ≥0`: costo logístico unitario aprobado de despacho. Valor predeterminado para comparación: kilómetros recorridos; si se usa combustible u otra dimensión, generar **otra métrica con sus unidades** y no mezclarlas sin conversión.
- `t0`: instante de corte de datos; `network_snapshot_id`: versión de red y bloqueos.

### 3.3 Pesos humanitarios y equivalencia entre necesidades

Para cada zona `i`, sea `A_i` el conjunto de necesidades **positivas y respaldadas** de bienes y unidades. Definir pesos relativos **dentro de cada zona**, `ω_ir ≥0` y `ω_ik ≥0`, con:

`Σ_{r:q_ir>0} ω_ir + Σ_{k:n_ik>0} ω_ik = 1` para `A_i≠∅`.

El valor predeterminado de demostración asigna igual peso a cada necesidad activa respaldada. Si existen pesos según criticidad de recurso/tipo de equipo, deben provenir de un perfil **versionado y justificado**; no inventar reglas clínicas de triaje. La normalización intrazona evita aumentar automáticamente el máximo beneficio de una zona sólo porque reportó más categorías de necesidad. Ninguna de estas ponderaciones es una estimación de muertes evitadas.

## 4. Variables de decisión (MVP)

- `x_vir ≥ 0`: cantidad de bien `r` transportado por `v` hasta zona `i` en su unidad propia. `x` es entera si r representa bienes indivisibles (kits), y continua si r es divisible (litros de agua), respetando precisión definida.
- `y_vi ∈ {0,1}`: 1 si vehículo de carga `v` realiza una salida al destino `i`.
- `z_uik ∈ {0,1}`: 1 si unidad especializada `u` se destina a zona `i` para misión `k`.
- `h_ir ≥0`, `g_ik ≥0`: faltantes de carga y de unidades (definidos mediante igualdades de balance).

No usar `x` fraccionaria para ambulancias, excavadoras o kits indivisibles. Las unidades especializadas `z` representan activos completos y misiones, no personas individuales sometidas a triaje.

## 5. Restricciones duras

**R01 Demanda de bienes:** `Σ_v x_vir + h_ir = q_ir` para cada demanda conocida `q_ir ≥0`; si demanda falta, no crear la igualdad con cero: mantener bandera de verificación fuera del solver.

**R02 Stock de cada depósito:** `Σ_{v:o(v)=d} Σ_i x_vir ≤ s_dr` para cada depósito `d` y bien `r`.

**R03 Activación de salida:** `0 ≤ x_vir ≤ q_ir · y_vi` si `q_ir` es conocido y positivo. Para bienes y combinaciones no elegibles, `x_vir=0`.

**R04 Una salida y un destino por vehículo en cada ciclo:** `Σ_i y_vi ≤ 1` por vehículo. Un vehículo no está disponible en otra corrida concurrente mientras su compromiso no se libere.

**R05 Capacidad física peso:** `Σ_{i,r} m_r x_vir ≤ W_v` por vehículo.

**R06 Capacidad física volumen:** `Σ_{i,r} b_r x_vir ≤ B_v` por vehículo.

**R07 Compatibilidad:** para cargas incompatibles (`compatible_vr=0`), fijar `x_vir=0`. Para material peligroso/refrigerado no modelado, declarar clase como no apta en el MVP.

**R08 Red vial, ventana y disponibilidad:** `y_vi=0` para `i ∉ E_v`, rutas con estado bloqueado/desconocido, vehículo no disponible o `T_vi>H`. Una ruta autorizada debe incluir acceso desde el depósito y sus restricciones conocidas, no usar distancia euclidiana en lugar de ruta vial verificada.

**R09 Equipo especializado no duplicado:** `Σ_{i,k} z_uik ≤ 1` por unidad `u`; `z_uik=0` si falta cualificación, disponibilidad o acceso válido en horizonte.

**R10 Demanda de unidades especializadas:** `Σ_u z_uik + g_ik = n_ik` para cada demanda conocida de tipo `k` y zona `i`.

**R11 Activo físico compartido:** para vehículos/unidades con un mismo `physical_asset_id`, la suma de sus activaciones en la corrida debe ser `≤ 1` (construir el conjunto de activaciones por identidad física), a fin de no despachar una ambulancia simultáneamente como transporte de bienes y unidad clínica.

**R12 Estado del escenario y legalidad:** sólo inputs de la misma emergencia y snapshot; cargas y tiempos ≥0, valores finitos, conversiones de unidades compatibles, cantidad entera cuando corresponde. Si el inventario, las rutas o las autorizaciones cambian durante la planificación, los resultados pasan a estado `STALE` y requieren recálculo antes de confirmar.

**R13 Demandas desconocidas:** una demanda `NULL` produce una `verification_needed` y no un despacho de cantidad supuesta; puede ser tratada en un **escenario explícitamente exploratorio** separado, nunca como recomendación confirmable.

## 6. Función objetivo: optimización lexicográfica

### Etapa 1 — cobertura humanitaria (maximización)

Para cada zona con demandas respaldadas, definir fracciones de cobertura `f_ir=(Σ_v x_vir)/q_ir` cuando `q_ir>0`, y `a_ik=(Σ_u z_uik)/n_ik` cuando `n_ik>0`. Son números en `[0,1]`.

`H(x,z)=Σ_{i:A_i≠∅} p_i · (Σ_{r:q_ir>0} ω_ir f_ir + Σ_{k:n_ik>0} ω_ik a_ik)`.

Maximizar `H(x,z)` sujeto a R01–R13.

`H` es adimensional. Para el mismo escenario y perfiles, mayor H significa mayor **cobertura ponderada por la prioridad de la zona**; no es una cantidad de personas salvadas ni una certeza causal. `p_i=0` no habilita ignorar necesidades confirmadas: se conserva déficit y puede existir una regla humana de atención obligatoria, pero un mínimo de cobertura es una **restricción adicional que exige justificación y examen de factibilidad**. No imponer mínimos imposibles.

Los coeficientes son constantes durante una corrida: `p_i` y `ω` congelados en snapshot. `H` es lineal en `x,z`. Los denominadores `q_ir,n_ik>0` son parámetros, nunca variables.

**Advertencia sobre equidad:** aunque los pesos intrazona evitan premiar reportar más tipos de necesidad, una optimización maximiza cobertura ponderada y puede dejar zonas sin atender. Proporcionar cobertura por zona y zona crítica sin asignación como alerta. Umbrales de equidad/mínimos serán, como opción, restricciones blandas con penalización y aprobación experta en una versión futura; no inventar un umbral ético obligatorio para el MVP.

### Etapa 2 — eficiencia logística sin sacrificar el objetivo anterior

Sea `H*` el mejor objetivo humanitario **obtenido por el solver** y su estado de optimalidad. Resolver:

Minimizar `C(y,z)=Σ_{v,i} c_vi y_vi + Σ_{u,i,k} c_ui z_uik`, sujeto a R01–R13 **y** `H(x,z) ≥ H* − ε_H`.

`ε_H` es una tolerancia numérica **pequeña y versionada**, nunca un margen para reducir deliberadamente la atención. Para prototipo en unidades adimensionales usar `ε_H=1e-8` si tolerancias y solver lo permiten; registrar valor usado y evitar tolerancia mayor que diferencias humanitarias que se pretende preservar. Si es necesario, normalizar o fijar el objetivo con política técnica documentada.

Si la Etapa 1 termina por límite de tiempo con solución factible pero no óptima, etiquetar `FEASIBLE_NOT_PROVEN` y considerar `H*` como **incumbente**; jamás publicar la solución como óptima global. La Etapa 2 sólo puede continuar bajo una política de uso de incumbentes explícita. Si se agota el tiempo sin solución, no generar asignaciones ficticias.

Si la segunda etapa falla, puede conservarse una solución factible de la primera etapa **sólo con rutas directas previamente verificadas**, señalándola como `LOGISTICS_NOT_OPTIMIZED` y con aprobación humana pendiente. No interpretar esta reserva como despacho automático ni como CVRP resuelto.

### Nota sobre unidades especializadas y costos

`c_ui` cuenta la salida de la unidad especializada exactamente una vez; `z_uik` sólo puede activar una misión. Si en futuro una unidad requiere carga en un vehículo ya representado, modelar la dependencia explícita para no contabilizar dos veces movimientos ni capacidades.

## 7. Privación temporal: cómo evitar contar el tiempo dos veces

Fase 4 **ya incluye tiempo sin asistencia** en el criterio `C7`, que contribuye a `p_i`. Por tanto, en la versión `optimization-v1` **NO multiplicar** adicionalmente `p_i` por otra función de horas de privación, ni sumar de manera automática `p_i·deprivation_cost` dentro de H. Esto introduciría doble conteo temporal y sesgo difícil de auditar.

No obstante, registrar un **KPI informativo de privación no evitada**, separado del objetivo:

`D_report = Σ_{i,r esencial} κ_r · (h_ir / q_ir) · φ_r(t_ir + H)` con `φ_r(t)= (t/T_ref,r)^γ_r`, `γ_r>1`, para necesidades activas confirmadas y `q_ir>0`.

`κ_r`, `T_ref,r`, `γ_r` se configuran explícitamente y **NO representan precios, mortalidad real ni parámetros clínicos validados**. Este KPI adimensional permite sensibilidad y discusión académica, no genera directamente decisiones en `optimization-v1`. Si se quisiera introducir `deprivation_cost` dentro del objetivo en versión 2, debe revisarse/redefinirse C7 en la Fase 4, calibrar y contrastar pesos, y versionar el cambio. La medición de privación presupone un horizonte y no simula tiempos reales de llegada de todas las entregas en la primera versión.

## 8. Rutas, viajes, CVRP y seguridad de factibilidad

### 8.1 Ruteo obligatorio MVP (una parada)

Antes de crear la variable `y_vi` elegible se calcula sobre la red PostGIS/servicio de rutas aprobado un trayecto legal y verificable `o(v)→i` y, si corresponde, `i→o(v)`. Guardar distancias, tiempos, arcos, versiones y restricciones. En la fase 2, el costo usa ese trayecto. Ruta `UNKNOWN`, bloqueada o que excede `H`: no elegible para plan confirmable.

El vehículo puede transportar distintos tipos de recursos compatibles **hasta una única zona** en su salida. La carga combinada respeta kg y m³; esto evita el error de sumar cantidades de tipos con unidades distintas sin conversión.

### 8.2 Extensión CVRP multi-parada (fuera del núcleo mínimo)

La ampliación propone rutas de múltiples paradas, pero requerirá: nodos visitados y cantidades, flujo por tramo, capacidades al salir y tras cada entrega, ventanas/tiempos, rutas de ida/regreso, compatibilidades y accesos, y decisión explícita sobre entregas divididas. Puede implementarse con OR-Tools Routing Solver o MILP integrado según volumen de escenarios y garantías deseadas. La documentación oficial de OR-Tools describe CVRP y restricciones de capacidad: https://developers.google.com/optimization/routing/cvrp .

**No permitido:** optimizar primero las cantidades con vehículos virtualmente infinitos y luego afirmar que un CVRP imposible de resolver implementa el mismo plan. Si la extensión multi-parada no encuentra rutas, debe reabrir asignación con restricciones/realimentación y generar una nueva recomendación (o conservar el plan directo verificable), nunca mostrar una ruta inventada. OR-Tools Routing puede entregar soluciones heurísticas, no siempre demostraciones de optimalidad; registrar estado y límites. No afirmar el mismo óptimo humanitario que el MVP directo cuando el conjunto de rutas factibles haya cambiado.

### 8.3 Restricciones vial/operacional de alto impacto

- No inferir transitabilidad de líneas rectas ni de OpenStreetMap desactualizado.
- El modelo no puede certificar condiciones viales reales; “ruta verificada” en simulación significa verificada **dentro del escenario**, no verificada por autoridad en terreno.
- Si se descubre un bloqueo, invalidar recomendaciones dependientes de ese arco y recalcular; preservar historia.
- Transporte por helicóptero, transporte marítimo y rutas desconocidas requieren perfiles/motores propios; no simularlos como calles transitables.

## 9. Gestión de información incompleta y sesgo territorial

- Demanda `NULL` no es cero. No estimar cantidades automáticamente con el score TOPSIS. Mantener `needs_verification` y reportar cobertura calculable sólo sobre necesidades conocidas/estimaciones aprobadas, con procedencia.
- Incertidumbre territorial alta NO justifica por sí misma una carga material o vehículo de rescate. Permitir recomendar **reconocimiento/verificación** como tipo de solicitud humana separada; no atribuirle cantidades de ayuda inexistentes.
- `score_lower`/`score_upper` de Fase 4 permiten análisis de robustez: repetir la solución en escenarios inferior/central/superior. No etiquetar dichos escenarios como pronóstico estadístico.
- Zonas sin recursos asignados deben aparecer en resultados incluso si hubo optimización global: `uncovered_critical_zones`, `unknown_demand_zones`, `low_connectivity_flags`.
- Ante múltiples emergencias, stock, flota, presupuesto y decisiones deben vincularse a una **reserva global coherente** para no usar el mismo activo dos veces.

## 10. Recomendación, autorización y auditoría

`Recommendation` tiene ID/version, escenario, resultado matemático, caducidad de datos, perfil humanitario/logístico, trayecto y alertas. Estados admitidos: `GENERATED`, `UNDER_REVIEW`, `ACCEPTED`, `MODIFIED`, `REJECTED`, `STALE`. Un plan `ACCEPTED` representa una decisión aprobada en el prototipo; no es automáticamente un despacho real.

Toda aceptación/modificación requiere usuario/rol autorizado, hora y justificación cuando cambian restricciones o cantidades. Antes de aceptación validar versiones y stock aún libre; si el inventario o estado de rutas cambió, devolver `STALE_REQUIRES_REOPTIMIZATION`. Registrar decisión humana en entidad separada de recomendación y no descontar inventario por la mera sugerencia.

## 11. Estados del solver y manejo de errores

- `OPTIMAL`: etapa resuelta y certificado óptimo por backend empleado dentro de tolerancias.
- `FEASIBLE_NOT_PROVEN`: solución factible, sin prueba de óptimo; incluir brecha y límite temporal cuando sea posible.
- `NO_FEASIBLE_SOLUTION`: restricciones obligatorias incompatibles, sin plan admisible.
- `NO_SOLUTION_FOUND`: no se encontró solución factible antes del límite; NO equipararlo a infactible.
- `MODEL_INVALID`: unidades/parámetros/datos contradictorios o falta configuración.
- `SOLVER_ERROR`: fallo técnico.
- `LOGISTICS_NOT_OPTIMIZED`: etapa 1 factible y rutas directas verificadas, etapa 2 no concluida.
- `NO_AVAILABLE_RESOURCES`: se permite solución de cero entregas, déficits positivos, advertencia específica; no declarar infactible salvo que existan mínimos duros.

Resultados deben separar status de etapa 1, etapa 2 y validación física de rutas. Tiempos de solver y cota/gap deben almacenarse; las bibliotecas y versiones afectan determinismo, guardar versión e incluso parámetros de semillas cuando correspondan.

## 12. Datos de ejemplo, cálculo verificable y baseline

Fixture sintético: una emergencia con dos zonas `Z01=Norte`, `Z03=Rural aislada`, prioridades congeladas **tomadas únicamente como números sintéticos del ejemplo de la Fase 4** (`p_N=0.778734`, `p_R=0.654473`). Un depósito con **3 kits** en stock. Cada zona necesita **2 kits** confirmados; sólo existe un tipo de necesidad para cada zona, de modo que `ω=1`. Dos vehículos desde el mismo depósito, cada uno transporta **máximo 2 kits**, 1 zona por vehículo, con rutas verificadas y retorno. Distancias unidireccionales: 10 km a Norte, 30 km a Rural. Por tanto, km de ciclo ida+retorno: 20 y 60.

**Solución humanitaria:** enviar 2 kits a Norte y 1 a Rural (`H* = 0.778734·(2/2)+0.654473·(1/2)=1.1059705`). Como existen solo 3 kits, no se puede satisfacer ambas zonas. Un baseline FIFO con solicitud rural registrada primero entrega 2 a Rural y 1 a Norte (`H_FIFO=0.654473+0.778734/2=1.04384`). Diferencia ilustrativa `(H*−H_FIFO)/H_FIFO≈5.9521 %` **en H de este escenario creado**, no en tiempo de respuesta, mortalidad ni calidad de vida real.

**Etapa logística:** hacen falta dos vehículos, uno hacia cada zona, por lo que el kilometraje total mínimo del plan humanitario es **80 km** (20 + 60). El escenario usa tiempos verificados que caben dentro del horizonte. El solver podrá elegir qué ID de vehículo se destina a cada zona si son idénticos; para reproducibilidad de la fixture debe imponer desempate estable por ID al *presentar*, sin introducir cambios materiales en el objetivo humanitario.

Para este caso, el déficit después de SIPRE es `Z01: 0 kit; Z03: 1 kit`. Baseline: `Z01:1 kit; Z03:0 kit`. Demanda global = 4; stock=3; cobertura física = 75 % con ambos, pero cobertura humanitaria ponderada difiere. **No confundir H con porcentaje de cobertura física.** El fichero `SIPRE_OPTIMIZACION_EJEMPLO.json` contiene estas cifras con seis decimales de precisión de entrada y un tolerancia de salida definida.

## 13. Baseline formal para fase experimental

`FIFO-FEASIBLE`: ordenar solicitudes por `reported_at` y `request_id`, y para cada una asignar el máximo factible según stock, capacidades, compatibilidad, rutas y horizonte; elegir el vehículo factible con menor coste de la corrida, con empate por `vehicle_id`; no saltar validaciones físicas. Permitir cubrir la solicitud parcialmente si el stock restante no alcanza. Cuando una solicitud requiere varios vehículos, continuar según disponibilidad.

**Advertencia:** la estrategia FIFO no es necesariamente el procedimiento real de SENAPRED/COGRID. Es un baseline **sintético y explícitamente no optimizado**, elegido para validar el modelo; evitar llamarlo “método actual chileno” o concluir superioridad frente a procesos institucionales reales.

El baseline debe usar exactamente los **mismos datos, rutas, inventarios y restricciones** que SIPRE. Definir en Fase 7 controles experimentales adicionales (orden de llegada, recursos escasos, desvíos y escenarios con prioridad invertida).

## 14. Diseño de API, esquema de resultados y Metabase

Entrada conceptual `OptimizationInput`:

```json
{
  "emergency_id": "E01", "scenario_id": "S01", "priority_run_id": "PR01",
  "as_of_time": "2026-10-16T12:00:00-03:00",
  "planning_horizon_hours": 6,
  "profile_version": "optimization-v1-demo",
  "inventory_snapshot_id": "INV01", "network_snapshot_id": "ROAD01",
  "zones": [], "demands": [], "depots": [], "vehicles": [], "units": [], "routes": [],
  "solver_config": {"stage1_seconds": 30, "stage2_seconds": 30, "objective_epsilon": 1e-8}
}
```

Salida `OptimizationResult`:

```json
{
  "optimization_run_id": "OPT01", "source_priority_run_id": "PR01",
  "stage1_status": "OPTIMAL", "stage2_status": "OPTIMAL",
  "humanitarian_objective": 1.1059705, "logistic_objective_km": 80,
  "shipments": [], "team_assignments": [], "unmet_demands": [],
  "routes": [], "unknown_demands": [], "uncertainty_flags": [],
  "recommendation_state": "GENERATED", "requires_human_approval": true,
  "model_version": "optimization-v1", "explanation": [], "audit": {}
}
```

Tablas/vistas BI esperadas para Fase 6: `optimization_run`, `optimization_shipment`, `optimization_team_assignment`, `optimization_unmet_demand`, `optimization_route`, `optimization_constraint`, `optimization_explanation`, `decision` (separada), y vistas de Metabase `vw_humanitarian_coverage`, `vw_demand_coverage`, `vw_logistics_km`, `vw_unmet_critical_demand`, `vw_zone_assignment_summary`, `vw_baseline_comparison`. **Nunca poner a Metabase a escribir decisiones operacionales**, sólo lectura y filtros.

Almacenar los datos fuente y sus versiones en tablas de auditoría/snapshots, junto con `solver_backend`, `solver_version`, `time_limit`, `objective_value`, `best_bound`, `gap`, `status`, `tolerance`, `run_at` y `approved_by` (si existiera decisión separada). Prohibido imprimir información clínica identificable en logs.

## 15. Validación y pruebas de aceptación para Codex

| ID | Prueba | Resultado esperado |
|---|---|---|
| P5-T01 | Fixture dos zonas/tres kits | `H*=1.1059705`, envíos Norte 2/Rural 1; km=80. |
| P5-T02 | Baseline FIFO sobre el fixture | envíos Rural 2/Norte 1; `H_FIFO=1.04384`. |
| P5-T03 | Stock cero | envíos 0, déficit total, status de recursos agotados (no falso error). |
| P5-T04 | Stock total insuficiente | ningún recurso asignado por encima del inventario. |
| P5-T05 | Vehículo con peso insuficiente | no exceder `W_v`. |
| P5-T06 | Vehículo con volumen insuficiente | no exceder `B_v`. |
| P5-T07 | Bien indivisible | nunca enviar cantidades fraccionarias de kits. |
| P5-T08 | Bien divisible | permitir cantidad decimal válida en litros cuando lo permita configuración. |
| P5-T09 | Recurso incompatible | x=0 para combinaciones vetadas. |
| P5-T10 | Ruta bloqueada | no usar arco ni despacho afectado. |
| P5-T11 | Ruta desconocida | no declararla válida; generar solicitud de verificación. |
| P5-T12 | Horizonte excedido | bloquear salida aun si distancia euclidiana es corta. |
| P5-T13 | Unidad especializada indivisible | z binario y equipo completo, no doble asignación. |
| P5-T14 | Unidad sin cualificación | no asignar misión incompatible. |
| P5-T15 | Activo físico representado dos veces | no despachar simultáneamente como camión y ambulancia. |
| P5-T16 | Demanda NULL frente a 0 observado | NULL→verificación; 0→sin necesidad; no imputar cantidades. |
| P5-T17 | Incertidumbre alta con demanda no confirmada | no generar automáticamente despacho de cantidad inventada. |
| P5-T18 | Etapa 2 lexicográfica | H de plan final ≥ H*−εH. |
| P5-T19 | Etapa 2 falla | solución factible de etapa 1 permanece claramente rotulada, o ninguna si no existen rutas verificadas. |
| P5-T20 | Infeasible vs timeout vs cero stock | salidas/estados distintos. |
| P5-T21 | Snapshot de inventario/red cambia | recomendación obsoleta no se confirma sin recalcular. |
| P5-T22 | Misma entrada/versiones | mismo valor de objetivos y cantidades; empate documentado. |
| P5-T23 | Demanda no cubierta | h_ir=q_ir−entregado≥0; incluir todas las zonas. |
| P5-T24 | Convergencia KPI vs objective | H no confundido con porcentaje físico o personas salvadas. |
| P5-T25 | No automación de mando | solver no marca `CONFIRMED`, no dispara órdenes ni sustrae stock definitivo. |
| P5-T26 | Contaminación entre emergencias | ningún stock, unidad o decisión de otra emergencia se incorpora sin vínculo explícito. |
| P5-T27 | Privación temporal | C7 representa tiempo; KPI de privación no se suma a H en la versión v1. |
| P5-T28 | Cambio de prioridad | con demandas/stock fijos puede modificar orden humanitario, sin violar factibilidad. |

## 16. Relación con la pauta y criterios de cierre

- **Innovación (30):** vincula ranking AHP-TOPSIS, incertidumbre y MILP lexicográfico explicable; muestra el beneficio de no decidir sólo por distancia.
- **Impacto social (20):** compara cobertura ponderada, déficit y alertas territoriales; no presume vidas salvadas.
- **Prefactibilidad y ambiente (20):** combina reposición limitada, capacidad y kilómetros como KPI; los efectos en energía/emisiones son hipotéticos hasta medirse con supuestos explícitos.
- **Viabilidad técnica (20):** restricciones que hacen viable un plan, soporte de un solver disponible, rutas verificadas del escenario y tests reproducibles.

**Listo para cerrar Fase 5 como diseño** cuando: ecuaciones y restricciones no tienen contradicciones internas, el fixture puede resolverse manualmente, la jerarquía lexicográfica queda explícita, los fallos tienen estados claros y existe un prompt de Codex que no invente las decisiones por su cuenta. **No significa que SIPRE ya esté validado para uso real**.

## 17. Decisiones que requieren validación posterior

1. Clasificación y unidades concretas de recursos, y pesos/volúmenes por unidad.
2. Gobernanza de tipos de unidad (ambulancia, maquinaria, cuadrilla) y calificación.
3. Criterio de demanda “confirmada/estimada aprobada” y responsables de aprobar estimaciones.
4. Valores `ω_ir`, `ω_ik`, umbrales de equidad, aceptación de cobertura parcial.
5. Horizonte por corrida, tiempos de viaje/descarga y obligación de retorno a base.
6. Permisos y proceso operativo de aprobación, inventario global y caducidad de ruta.
7. Información vial operativa verdaderamente disponible; sin verificaciones externas sólo hay prototipo simulado.
8. Objetivos de privación temporal validados y costo de privación (sin doble contar con C7).
9. Definición y viabilidad de CVRP multi-parada si pasa a MVP avanzado.
10. Tamaño computacional máximo y límites realistas de tiempo tras benchmarks.

### Fuentes técnicas externas (para implementación, no validación del sistema)

- Google OR-Tools: [Vehicle Routing Problem with capacity constraints](https://developers.google.com/optimization/routing/cvrp).
- Google OR-Tools: [Common routing tasks, time limits and search](https://developers.google.com/optimization/routing/routing_tasks).
- Investigación SIPRE aportada por el usuario en fase anterior: insumo conceptual de AHP–TOPSIS y optimización humanitaria; los coeficientes y simplificaciones de este documento son decisiones adicionales de diseño, no valores oficiales.
