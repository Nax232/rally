# SIPRE — Fase 7: Protocolo experimental preregistrado (diseño)

**Archivo:** `SIPRE_EXPERIMENTOS_v1.md`  
**Versión:** `experiment-protocol-v1.0`, 2026-10-16  
**Estado:** especificación de diseño lista para revisión; **ninguna simulación de este protocolo ha sido ejecutada**.  
**Responsables:** ChatGPT (diseño), equipo humano (aprobación y congelamiento), Codex (implementación y ejecución posteriores).  
**Fuentes de verdad previas:** `SIPRE_PRIORIZACION_v1.md` (F4), `SIPRE_OPTIMIZACION_v1.md` (F5), `SIPRE_ARQUITECTURA_v1.md` (F6), Fases 2–3 en la conversación.  
**Uso permitido:** prototipo académico con datos simulados; no representa una validación en catástrofes reales ni certifica la aptitud para uso institucional.

## 0. Objetivo y reglas de integridad

Evaluar **sobre los mismos snapshots reproducibles** cómo se comporta SIPRE (TOPSIS anclado + MILP lexicográfico de una salida/vehículo y destino único) frente a un **FIFO factible y determinista** (`FIFO_FEASIBLE`). Se medirán desempeño humanitario, cobertura, déficits, tiempo de cómputo, equidad indicativa, distancia y robustez bajo escasez, cortes de ruta y datos incompletos.

**Prohibiciones:** cambiar datos/semillas/baseline/función de éxito tras observar resultados; simular que un camino desconocido está abierto; usar inventarios distintos entre métodos; construir métricas sumando litros + kits + personas; considerar H «vidas salvadas»; declarar un CVRP multiparada; utilizar datos ocultos como input del algoritmo; presentar rutas de simulación como rutas verificadas en terreno; equiparar mejora del objetivo matemático con impacto real demostrado.

**Reglas rectoras:** `SIMULATED=true`; una salida y un destino por vehículo disponible; instantáneas idénticas por par, perfiles versionados y sin cambios; H humanitario antes que kilómetros; el motor propone y nunca despacha; Metabase consulta datos en `analytics` mediante cuenta de sólo lectura.

## 1. Pregunta, hipótesis y resultados previstos (no asumidos)

Pregunta: «En escenarios sintéticos de post-emergencia con recursos limitados, ¿cuánto mejora SIPRE la cobertura humanitaria ponderada respecto de una política FIFO factible, y qué compromisos presenta en kilómetros, demandas críticas desatendidas, equidad y tiempo computacional?».

- **H1 de evaluación:** para las instancias preregistradas, SIPRE obtiene mayor media de `H_norm` y/o menor déficit de cobertura crítica que FIFO_FEASIBLE, sin vulnerar restricciones. No se asume que ambas métricas mejoren ni que el ahorro logístico sea positivo.
- **H0:** no hay mejora observada de `H_norm` ni del indicador de cobertura crítica frente a FIFO_FEASIBLE en los pares definidos.
- **Hipótesis operacionales:** para ambos métodos, cero violaciones duras y cero despachos automáticos. La factibilidad es condición de validez, **no** un resultado que se intercambie por mejor H.
- **Hipótesis secundarias exploratorias:** sensibilidad a la escasez, al aislamiento y a los datos faltantes. No se asume reducción de kilómetros en escenarios donde SIPRE decide atender zonas más lejanas.

Importante: si la etapa 1 de SIPRE se certifica `OPTIMAL` y FIFO ofrece un plan factible en el mismo conjunto de restricciones, es **matemáticamente esperable** que `H_SIPRE >= H_FIFO - tolerancia`. La contribución de la evaluación será cuantificar el tamaño, costo y estabilidad de la diferencia, así como revelar sesgos, déficits y tiempos; **no presentar esta desigualdad como descubrimiento científico independiente**.

## 2. Versión de modelos congelados

**Fase 4:** ocho criterios `C1...C8`; AHP con `RI_8=1.41`, `CR<=0.10`; para perfil DEMO `w8<=0.08`; TOPSIS anclado en ideales (1) y antiideales (0); `p_i ∈ [0,1]`; cada zona conserva puntuación, rango, incertidumbre y factores. **C7 ya incorpora tiempo de privación:** en F5 no se multiplica adicionalmente por penalizador temporal. `p_i` no es probabilidad clínica.

**Fase 5:** maximización lexicográfica de `H=Σ_i p_i Σ_{j∈A_i} ω_ij·coverage_ij`, donde las necesidades activas conocen demanda positiva y `Σ_j ω_ij=1` por zona. Etapa 2 minimiza `C` con `H≥H*−ε_H`, perfil de demo `ε_H=1e−8` sujeto a la tolerancia real del solver. Una salida y un destino por vehículo; ruta explícitamente `VERIFIED_OPEN` o `VERIFIED_RESTRICTED` dentro del escenario; no `UNKNOWN` o `BLOCKED`. Respetar R01–R13, capacidades en kg/m³, stocks por depósito y unidades especializadas indivisibles. Solver registra óptimo probado, incumbente factible, timeout, gap o sin solución con categorías **distintas**.

**Extensiones expresamente fuera del experimento principal:** CVRP multiparada, IA generativa, predicción de víctimas, rutas en vivo, datos de ALFA/FIBE en tiempo real, respuesta médica individual, despacho automático o sincronización distribuida offline.

## 3. Diseño experimental comparativo

Diseño factorial por **cuatro familias de escenarios**. Comparación **pareada**: cada archivo sintético de escenario se ejecutará una vez por método (o se reutilizará un resultado determinista validado). Método es la variable independiente principal (`FIFO_FEASIBLE`, `SIPRE`). Variables de estratificación: escasez, bloqueo y datos faltantes. La semilla determina los datos de la familia, no los resultados a favorecer.

**Muestra confirmatoria diseñada:** 12 semillas fijas por familia: `101,102,103,104,105,106,107,108,109,110,111,112`. Total previsto: **48 instancias x 2 métodos = 96 ejecuciones comparables**, excluyendo regresiones y estrés. Ejecutarlas cuando el software esté implementado. No modificar N dependiendo de p-valores/resultados. Si el costo computacional impide completarlas, declarar la limitación y número de pares realmente obtenidos; no hacer reemplazo selectivo.

**Piloto técnico separado** (no confirmatorio): dos fixtures de regresión F4/F5 y 1 instancia por familia con semillas `1–4`. Sirven para probar el pipeline, no para calibrar escenarios y luego tratarlos como resultados confirmatorios. Si el piloto revela un error de protocolo, aprobar una versión nueva (`v1.1`) **antes** de iniciar cualquier corrida confirmatoria, guardar ambos y documentar cambios. No corregir post hoc el baseline para perjudicarlo o favorecerlo.

Todas las ejecuciones de un mismo par usan: idéntica emergencia, `snapshot_id`, `as_of_time`, geometría, red vial/versiones, rutas autorizadas, inventario libre, flota, horario, demanda observada y aprobada, prioridades provenientes de **una misma corrida F4** y pesos `ω`. FIFO no puede obtener información adicional ni menos permisos de acceso que SIPRE. Los resultados no alteran el inventario base: cada ejecución se realiza sobre una **copia lógica** de la misma instantánea, sin registrar reservas compartidas ni decisiones finales.

## 4. Familias sintéticas preregistradas

Todas ocurren dentro de las **primeras 72 h** posteriores a un desastre ficticio. No atribuir a ciudades o personas reales. Los rangos siguientes son **parámetros DEMO sintéticos**, no estimaciones nacionales:

| ID | Caso | Zonas | Vehículos carga | Equipos indivisibles | Oferta/demanda conocida por tipo (objetivo) | Perturbación controlada | Pregunta |
|---|---|---:|---:|---:|---|---|---|
| E01 | Moderada | 8 | 6 | 3 | entre 0.90 y 1.10 | conectividad alta, pocos cierres | distribución y H con recursos casi suficientes |
| E02 | Escasez severa | 12 | 5 | 2 | entre 0.40 y 0.60 | mayor demanda, flota escasa | cobertura crítica, déficit y justicia territorial |
| E03 | Red vial dañada | 10 | 6 | 3 | entre 0.70 y 0.90 | 25–40% de arcos no habilitados, verificar conectividad | no usar rutas bloqueadas e impacto del aislamiento |
| E04 | Datos fragmentados | 10 | 6 | 3 | entre 0.60 y 0.80 en demanda *visible* | 25–40% observaciones C1–C7 faltantes; demandas desconocidas | flags, intervalos y riesgo de zonas invisibles |

**Advertencia:** ratios son objetivos de generación y se verifican al construir los escenarios, no garantías de cobertura ni de factibilidad. Un vehículo sólo puede visitar una zona; muchos destinos pueden quedar sin atender incluso con suficiente stock. La categoría de necesidad `UNKNOWN` se excluye del objetivo ejecutable; no equivale a demanda nula.

Clases de recurso **mínimas**: `KIT` (entero; masa/volumen por unidad), `AGUA_L` (litros; masa/volumen definida), `RESCATE` (unidad de servicio especializado indivisible). Cada familia debe incorporar como mínimo dos depósitos, un grafo vial conectado de base (antes de bloqueos), tiempos/demanda por zona, vehículos con origen y capacidades físicas, y rutas marcadas explícitamente como verificadas dentro del **escenario**. Personas reportadas se usan sólo en indicadores agregados, sin datos personales.

**Caso E03:** construir grafo conectado de partida; seleccionar cierres con la semilla; recalcular caminos por vehículo desde su depósito y marcar `BLOCKED`/`UNKNOWN` donde corresponda. Puede existir zona crítica sin camino; se informa déficit, no se inventa traslado aéreo. Cuando el rango de cierres exceda la estructura y deje todo sin conexión, documentarlo; no descartarlo arbitrariamente.

**Caso E04:** generar primero una *verdad sintética oculta* (`synthetic_oracle`) y después un subconjunto observable (`observed_snapshot`) mediante máscara reproducible. Los métodos **sólo** reciben `observed_snapshot`. Evaluación retrospectiva contra oracle queda claramente separada de KPI de cobertura de necesidades conocidas. Los valores desconocidos permanecen NULL y se acompañan de `needs_verification`, amplitud `score_upper−score_lower` y banderas. **Prohibido** usar el oracle para asignar recursos.

### 4.1 Generador y congelamiento

El archivo adjunto `SIPRE_ESCENARIOS_CONFIG_v1.json` es el **manifiesto de generación**, no 48 escenarios ya generados. Codex debe convertirlo en un generador determinista que produzca fixtures **estables por `(scenario_family, seed, generator_version)`**, con `random.Random(seed)` o generador equivalente de algoritmo/versión fijados. Para asegurar reproducibilidad entre ejecuciones, guardar fixtures materializados `.json`, checksums SHA-256 y versión de Python/dependencias. No confiar sólo en repetir una semilla bajo distintos algoritmos.

El generador deberá tener al menos: (1) demanda y necesidades, (2) criterios de las ocho dimensiones y perfiles, (3) road graph y estado de arcos, (4) rutas factibles calculadas de acuerdo con F5, (5) stocks por depósito y flota, (6) timestamps con zona horaria, (7) una marca `SIMULATED`, (8) modo evaluable de información faltante en E04. Documentar distribuciones específicas, generador RNG y política de redondeo en `docs/experiment-generator.md` **antes del congelamiento**. Hasta que esto esté resuelto, la especificación es un diseño y no un fixture reproducible final.

## 5. Baseline congelado: `FIFO_FEASIBLE` (greedy por orden de reporte)

No se trata de un despacho real de SENAPRED. Es una **línea base algorítmica académica**, simple y deliberadamente factible. Reglas exactas para Codex:

1. Seleccionar solicitudes confirmadas o estimadas **aprobadas** con demanda positiva, ordenando por `(reported_at_UTC asc, request_id asc)`. Para necesidades conocidas de varios tipos en una zona, cada par `(zone_id, need_type)` tiene solicitud y timestamp; no reordenar por TOPSIS ni riesgo. Las unidades especializadas siguen la misma cola general.
2. Para cada solicitud, enumerar unidades/vehículos aún libres, stocks restantes y rutas elegibles conforme a las **mismas** restricciones R01–R13, horizonte y `snapshot` de SIPRE. No utilizar `UNKNOWN`/`BLOCKED`. Un activo físico sirve una sola vez.
3. Para bienes, elegir vehículo elegible y depósito con menor costo de ruta autorizado; desempatar por `vehicle_id`, luego `depot_id`. Cargar `min(demanda pendiente, stock disponible, capacidad residual peso/volumen)` con precisión correcta de recurso y sin violar compatibilidad. Un vehículo puede cargar distintos bienes para **la misma zona** dentro de su salida, sin segunda salida; si asignado a zona distinta, es inelegible. **No** optimizar combinaciones posteriores ni reordenar solicitudes para mejorar H.
4. Para equipo indivisible, elegir unidad compatible no asignada con ruta autorizada de menor costo; empatar por `asset_id`. Respetar identidad física compartida y horizonte.
5. Si no existe asignación legal, registrar déficit/alerta y continuar con la siguiente solicitud; no detenerse ni fabricar recursos. Al terminar, verificar plan con el mismo `feasibility_validator` que SIPRE.
6. Para todos los resultados, calcular `H` y costos con **exactamente el mismo evaluador matemático de F5**, jamás con otra fórmula. FIFO ignora la prioridad al **decidir**, pero la prioridad forma parte de la **evaluación de resultados**; de lo contrario no serían comparables.

Cuando una solicitud parcial pueda completarse por más de un vehículo elegible, continuar con el siguiente vehículo libre mientras exista capacidad/stock, sin más de una salida por vehículo. Orden estable de bienes a cargar por timestamp de solicitud, luego `request_id`. Si vehículo ya asignado a una zona, se puede aprovechar capacidad residual solamente para solicitudes posteriores de la *misma zona*, siempre que esto no implique segunda salida ni nueva ruta. **Invariante:** validar al final `Σ_destinos y_vi≤1` por vehículo y las restricciones F5. Es aceptable que FIFO tenga peor H, pero **no** una factibilidad artificialmente inferior por privilegios desiguales.

## 6. Indicadores (definiciones y tratamiento de denominadores)

**Unidad de comparación:** par `(scenario_id, seed)` con input congelado.

**Primario P1 — `H_norm` (adimensional [0,1]):** `H / H_max_theoretical`, donde `H_max_theoretical=Σ_{i con demanda activa conocida} p_i·Σ_{j activa}ω_ij`. Si no hay demandas activas o denominador cero, `NULL` / `NOT_APPLICABLE`, no 0 ni 100%. Este máximo ignora restricciones físicas y no es necesariamente alcanzable. Ambos métodos usan la misma referencia. Reportar también `H_raw` (puntaje F5), **sin llamarlo porcentaje de recursos o personas asistidas**.

**Primario P2 — `critical_need_coverage` ([0,1]):** promedio *por necesidad activa documentada* de `coverage_ij∈[0,1]` en zonas clasificadas `CRÍTICA` por perfil demo F4 (`p_i≥0.75`), con pesos iguales por par necesidad/zona. **No sumar litros + kits + ambulancias.** Si no hay necesidades críticas documentadas, valor `NULL/NOT_APPLICABLE`. Registrar también número de pares elegibles y número de zonas críticas sin ninguna asignación.

**Secundario S1 — déficit por recurso (`unmet_by_resource`):** `Σ_i(q_ir−fulfilled_ir)` por bien *separadamente*, con unidades (kits / L); `unmet_specialist[k]` para equipos enteros; no comparar o sumar déficits de unidades heterogéneas.

**Secundario S2 — cobertura media de necesidades conocidas (`mean_known_need_coverage`):** promedio no ponderado de fracciones cumplidas sobre pares (zona,tipo) con demanda >0, incluidos bienes y servicios de equipos con cantidades conocidas. Reportar número de pares.

**Secundario S3 — `total_route_km` y `total_route_hours`:** suma documentada de viajes de vehículos/unidades comprometidos bajo perfil de ruta; retorno incluido solamente si así define perfil (igual entre métodos). Unidades con ruta imposible no generan viaje ficticio. Si SIPRE atiende zonas más lejanas que FIFO puede aumentar km: reportarlo.

**Secundario S4 — `km_per_H_raw`:** `total_route_km/H_raw` sólo cuando `H_raw>0`, **indicador orientativo**, no sustituye comparación a beneficio similar. Para comparar eficiencia logística de la segunda etapa, además ejecutar controles con beneficio H fijado dentro de tolerancia y rutas factibles (ver §8), y medir km.

**Secundario S5 — utilización:** i) `used_vehicle_count/available_vehicle_count` y ii) `Σ carga_kg / Σ capacidad_kg_de_los_vehículos_usados`, separadas. La segunda no se define si no hay vehículos usados. No mezclar unidades especializadas con camiones para kg.

**Secundario S6 — verificabilidad / equidad indicativa:** `critical_zones_without_assignment`, `unknown_demand_zone_count`, `needs_verification_count`, amplitud de `score_upper−score_lower` en zonas con faltantes, mínimo de cobertura media por zona (sólo demandas conocidas), distribución de cobertura por zona; Gini opcional sólo si el conjunto de zonas comparadas y denominador están definidos y documentados.

**Secundario S7 — computación:** `priority_runtime_ms`, `stage1_runtime_ms`, `stage2_runtime_ms`, `total_pipeline_ms`, `peak_rss_mb` cuando medible en la plataforma (registrar método de medición, equipo y cargas concurrentes). No sumar tiempos mezclados de ejecución paralela no comparable.

**Secundario S8 — KPI demostrativo de privación no evitada:** calculado según F5 (función versionada), **fuera de H**. Etiquetar "indicador sintético no clínico"; si parámetros κ, T_ref y γ no están calibrados, no utilizarlo como prueba de vidas salvadas ni contaminación del objetivo.

### 6.1 Interpretación y comparaciones válidas

Para cada par guardar `ΔHnorm=Hnorm_SIPRE−Hnorm_FIFO` y `ΔCrit=coverage_crit_SIPRE−coverage_crit_FIFO`, expresados en **puntos porcentuales** si se multiplican por 100; `Δkm=km_SIPRE−km_FIFO`, positivo significa más km. También `Δunmet[r]` por recurso. Cuando un denominador es cero/NULL, reportar NA y el tamaño efectivo de muestras, no descartar el par sin documentarlo.

**NO** comparar distancias como si ambas estrategias prestaran igual servicio cuando H difiere. Describir compromisos: más kilómetros puede ser una decisión justificable para atender zonas de alta prioridad; menos km con peor atención no es eficiencia humanitaria por sí mismo.

## 7. Criterios de aceptación del experimento y de éxito (preregistrados)

### 7.1 Puerta de calidad (obligatoria, independiente del desempeño)

- 100% de las corridas **publicadas como válidas** pasan validación de stock, peso, volumen, rutas, una salida/destino, compatibilidad, identidad física y horizonte.
- 0 rutas `BLOCKED/UNKNOWN` asignadas; 0 demandas NULL convertidas a 0; 0 recomendaciones promovidas automáticamente a decisiones.
- 100% de pares ejecutados desde el **mismo** hash de snapshot y versiones de parámetros, y etiquetados `SIMULATED`.
- 100% de fallas del solver/timeout preservadas con estatus (`OPTIMAL`, `FEASIBLE_NOT_PROVEN`, `NO_SOLUTION_FOUND`, etc.). Nunca convertir timeout en 0 recursos y puntuarlo como óptimo.
- Validez de regresión F4 (17 pruebas) y F5 (28 pruebas) **antes** de cualquier ejecución confirmatoria, más tests del generador y FIFO.

### 7.2 Objetivos de éxito académicos (propuestos, no resultados)

- **Éxito humanitario de la comparación:** promedio de `ΔHnorm > 0` sobre pares evaluables y descripción completa de la magnitud y dispersiones por familia. No se exige que absolutamente todos los pares mejoren; reportar los que empaten o empeoren y los estatus del solver.
- **Éxito crítico complementario:** promedio de `ΔCrit ≥ 0` en pares donde esté definido; si empeora, informar trade-off y debatir si la función H requiere revisión para una **versión futura**, no alterarla después de observar resultados v1.
- **Éxito operativo:** 0 violaciones duras y una traza reproducible de cada corrida. Un `H` alto con rutas inviables **no cuenta**.
- **Éxito de viabilidad técnica:** ciclo completo de carga de escenario, priorización, baseline, optimización, persistencia y visualización Metabase demostrado con evidencias de ejecución. No se fija umbral de latencia no medido como promesa; se informarán p50, p95 y hardware.
- **Sustentabilidad:** km, utilización de vehículos y consumo energético estimado **sólo** con factor documentado; resultado ambiental puede ser neutro o desfavorable cuando se prioricen comunidades remotas.

Estas condiciones no equivalen a ensayo clínico ni piloto con COGRID; validan un simulador académico bajo supuestos establecidos.

## 8. Robustez, sensibilidad y pruebas negativas

**Confirmatorio:** las 48 instancias pareadas de §3 (si no hay bloqueos de ejecución). **Exploratorio aparte**, siempre etiquetado como tal:

1. **Sensibilidad de pesos:** tres perfiles AHP versionados: DEMO base, +20% relativo del peso C3 vulnerabilidad, +20% relativo del peso C5 accesibilidad; renormalizar los ocho pesos a suma 1 y registrar si w8 sigue ≤0.08. **No atribuir `CR` válido a estas perturbaciones:** si no provienen de matriz AHP aprobada, son únicamente perfiles de sensibilidad, no pesos institucionalmente autorizados.
2. **Incertidumbre:** repetir E04 con versiones inferior/estimada/superior de C1–C7; marcar salida como `EXPLORATORY`, no intervalos de confianza ni datos predichos.
3. **Robustez vial:** retirar un arco de ruta antes verificado y comprobar que el plan previo pasa a STALE y las rutas nuevas nunca cruzan el arco bloqueado.
4. **Robustez a stock:** fijar stock=0 y comprobar que plan sin asignaciones y déficit documentado es válido si no existen mínimos duros.
5. **Robustez a cambios de inventario:** dos aprobaciones humanas concurrentes no generan doble reserva; la recomendación obsoleta falla de forma transaccional. Este es test de sistema, no prueba estadística.
6. **Estrés de capacidad:** fixtures de 10, 30 y 100 zonas con semillas `501,502,503`, reportar tiempo p50/p95 con ≥10 repeticiones por tamaño, memoria y tasa de solver `OPTIMAL`/incumbentes (repeticiones no aumentan N de la comparación principal).
7. **Sensibilidad del optimizador a tiempos límite:** correr un subconjunto predefinido `[E02-101, E03-101, E04-101]` con límites 5s, 15s, 30s, conservando misma semilla/snapshot; diferenciar GAP/estatus. Elegir presupuesto final antes de las 48 instancias, sobre criterios técnicos y no resultados favorables.
8. **Escenarios adversos:** no hay rutas, todos datos faltantes, zero-demand, incompatibilidades, un depósito aislado, todas las unidades especializadas agotadas, expiración de rutas y vehículo con carga insuficiente. Deben producir resultados tipados, nunca traceback sin contexto.

## 9. Análisis estadístico y reporte

Unidad estadística: **instancia pareada** de semilla/familia, no cada viaje ni cada zona. Para KPI primarios: tabla por familia y global con N válido, media de diferencias pareadas, mediana, desviación, mínimo, máximo, p25/p75; proporción de pares SIPRE>FIFO, =, <. Visualizar puntos individuales o violines/histogramas sin ocultar dispersiones.

Opcional: **intervalos bootstrap percentil al 95%** sobre la media de diferencias, con re-muestreo **por instancia completa** dentro de cada familia (estratificado, por ejemplo B=5000 y semilla de bootstrap `90210`); estos intervalos ilustran variación entre escenarios sintéticos generados, **no generalizan estadísticamente a todos los desastres chilenos**. Registrar la proporción y los casos en que no se definió métrica. No presentar un p-valor como prueba de mejora social real.

Si SIPRE retorna `FEASIBLE_NOT_PROVEN`, reportar el plan factible y gap por separado, sin afirmar óptimo. Si no retorna solución, registrar fallo y no reemplazar por cero ni ocultar el escenario. Reportar análisis principal sobre **pares válidos y comparables**, más cuadro de intención de ejecución con todos los 48 IDs y causa de exclusión: evita selección conveniente.

**Advertencia de interpretación:** dado que H define lo que optimiza SIPRE, el criterio `H_norm` favorece naturalmente al modelo propuesto frente a FIFO. Complementar siempre con `critical_need_coverage`, déficits físicos por tipo, zonas no atendidas, km y equidad; la investigación no prueba ventajas frente a expertos humanos ni herramientas institucionales.

## 10. Registro y exportación de resultados

Datos persistidos en los esquemas de F6: `experiments.scenarios`, `experiments.runs`, `experiments.metrics`; `planning.optimization_runs` para SIPRE; `model.priority_runs`; tablas de rutas y déficit. Añadir a `experiments.runs` o tabla asociada campos (vía migraciones) para `scenario_family`, `seed`, `input_hash`, `parameters_hash`, `software_commit_sha`, `python_version`, `ortools_version`, `environment`, `method`, `run_status`, `started_at`, `finished_at`, `solver_stage1_status`, `solver_stage2_status`, `solver_gap`, `simulated=true`, `experiment_protocol_version`.

**CSV largo canónico `experiment_metrics_long.csv`:** `experiment_run_id,scenario_id,scenario_family,seed,method,metric_code,value,unit,status,protocol_version,fixture_sha256,software_commit_sha,simulated`. Una fila por KPI y ejecución; `value` vacío para NA, nunca sustituir por cero. Para unidades mixtas, agregar por recurso o mantener `resource_id` en columna opcional. **No** exportar datos personales.

**CSV ancho opcional `experiment_pairs.csv`:** par `(scenario_id,seed)` con `sipre_status`, `fifo_status`, `h_norm_sipre`, `h_norm_fifo`, `delta_h_norm`, `critical_coverage_sipre`, `critical_coverage_fifo`, `delta_critical_coverage`, `km_sipre`, `km_fifo`, `delta_km`, `comparable`, `exclusion_reason`.

**`experiment_manifest.json`:** guarda 48 hashes de fixtures, generador y versión, RNG/seeds, software commit, versión BD, pesos, topología, métodos, budget solver, límites de tolerancia, timestamp y entorno. Resultados ejecutados exportables a CSV/JSON con firmas de integridad SHA-256 y consulta de reconstrucción reproducible.

**Metabase:** `analytics.v_experiment_comparison` con `scenario_id, scenario_family, seed, method, metric_code, value, unit, status, version, simulated, run_at`; dashboard comparativo H_norm, cobertura crítica, km, déficit por unidad, flags/estado y costos; filtros por familia/seed; resultados de simulación inequívocamente etiquetados. No almacenar tokens de API ni fuentes sensibles en vistas.

## 11. Secuencia de ejecución obligatoria para Codex

1. Leer primero `AGENTS.md`, documentos F4–F7, repositorio y estado de Git. No inventar componentes existentes.
2. Verificar validación del plan F8 y arquitectura aprobada. Si no están, **preparar plan, no escribir implementación**.
3. Implementar generador determinista y materialización de 48 fixtures. Crear `docs/experiment-generator.md`, registrar decisiones pendientes con aprobación humana antes de congelamiento.
4. Implementar FIFO_FEASIBLE conforme §5 reutilizando validador común y métricas F5; escribir tests unitarios adversos.
5. Implementar calculadora de KPI independiente del método y versiones. Tests numéricos con fixtures F4/F5 de referencia.
6. Implementar persistencia `experiments.*`, manifiestos, SHA-256 y vistas analytics; asegurar Metabase de solo lectura.
7. Correr **piloto separado**, registrar resultados y corregir defectos de código/validaciones sin alterar reglas matemáticas. Si un cambio de protocolo es necesario: versionar nueva propuesta antes de corrida confirmatoria.
8. Congelar `protocol_version`, fixtures, parámetros, seeds y código; ejecutar 48 pares, registrar TODO (errores y exclusiones incluidas).
9. Exportar CSV/JSON y verificar checksums; crear reporte de ejecución factual **sin interpretación académica** (ésta será F17 ChatGPT).
10. Reportar comandos de ejecución, tests, hash de commit, hardware, librerías, brechas y fallas. No afirmar impacto real ni uso operacional autorizado.

## 12. Pruebas de aceptación de fase (F7-01 a F7-26)

| ID | Prueba | Criterio |
|---|---|---|
| F7-01 | Identidad de snapshot | FIFO y SIPRE consumen mismo hash y perfíl. |
| F7-02 | Determinismo generador | Igual family/seed/version produce mismos bytes/hashes. |
| F7-03 | Semillas confirmatorias | Se crean 48 IDs esperados sin repetidos. |
| F7-04 | Trazabilidad | Cada resultado referencia seed, commit, perfil, hash y red. |
| F7-05 | FIFO estable | Orden por UTC y request_id, sin leer TOPSIS para asignar. |
| F7-06 | FIFO factible | Misma validación R01–R13 que SIPRE, sin excepción. |
| F7-07 | Stock | Ningún método despacha más inventario. |
| F7-08 | Peso/volumen | Ningún método viola capacidad física. |
| F7-09 | Compatibilidad | No se asignan clases no compatibles. |
| F7-10 | Activos duplicados | Misma identidad física no se usa dos veces. |
| F7-11 | Rutas bloqueadas | Cero entregas por rutas BLOCKED/UNKNOWN. |
| F7-12 | Horizonte | Cero viajes fuera del horizonte autorizado. |
| F7-13 | Desconocidos | NULL no se traduce a cero o demanda inventada. |
| F7-14 | Privación | C7 y KPI no duplican factor temporal en H. |
| F7-15 | Evaluación H | H_FIFO y H_SIPRE usan idéntica función F5. |
| F7-16 | H normalizado | H/Hmax en [0,1] o NA si Hmax=0. |
| F7-17 | Cobertura heterogénea | No se mezclan litros y kits por suma de unidades. |
| F7-18 | Regresión mini fixture | Ejemplo F5 produce H y entregas previstas con tolerancia. |
| F7-19 | Solver statuses | Distingue OPTIMAL/FEASIBLE/NO_SOLUTION/INFEASIBLE. |
| F7-20 | Pares faltantes | Toda no-ejecución documentada; no omisión silenciosa. |
| F7-21 | No data leakage | Oracle E04 nunca pasa al baseline/priorización/optimizador. |
| F7-22 | Simulación visible | Toda salida se rotula SIMULATED, incluida Metabase. |
| F7-23 | Separación humana | Ejecución simulada nunca produce decisión/aprobación automática. |
| F7-24 | Exportaciones | CSV y JSON parseables, hashes calculados y rastreables. |
| F7-25 | Comparación logística | Diferencias de km se interpretan con cambio de H. |
| F7-26 | Perfil de seguridad BI | Metabase no tiene permisos de escritura y vistas no exponen PII. |

## 13. Matriz de evaluación de pauta

| Criterio | Prueba/entregable tangible |
|---|---|
| Innovación (30) | Comparativa AHP/TOPSIS+optimización versus FIFO factible; análisis de incertidumbre y escenario E04; demo de restricciones y explicaciones. |
| Impacto social (20) | Cobertura ponderada, cobertura de demandas críticas, déficits por clase, zonas excluidas; limitaciones sociales sin afirmar vidas salvadas. |
| Prefactibilidad/sustentabilidad (20) | Costos de recursos y flota, km, utilización, esfuerzo de despliegue y posible consumo estimado con factor explícito. |
| Viabilidad técnica (20) | 17+28 regresiones, 26 tests fase 7, exactitud de snapshots, reproducibilidad, estados del solver, rutas, persistencia y dashboards Metabase. |

## 14. Riesgos, salvaguardas y pendientes de aprobación humana

- Sesgo de confirmación: objetivo H elegido por SIPRE favorece al mismo SIPRE; métricas complementarias y discusión transparente. Baseline FIFO es benchmark simple, **no una reproducción histórica real de protocolos chilenos**.
- Modelado parcial: un destino por salida y una única ventana no captura reaprovisionamientos y tiempos dinámicos reales.
- Sesgos territorial/digital: datos faltantes no equivalen a baja vulnerabilidad; verificación separada, intervalos y evaluación retrospectiva E04.
- Equidad: H puede concentrar recursos; reportar mínima cobertura y zonas críticas sin asignación, aunque objetivo mejore.
- Inviabilidad: una ruta cerrada no se fuerza, un destino inalcanzable se documenta; zona crítica no implica ruta legal.
- Evidencia académica: parámetros sintéticos no validados con autoridades, ausencia de usuarios reales y datasets operacionales.
- Aprobaciones antes de F8/confirmatorio: política de generación detallada, peso/clases de recursos y `ω`, persistencia por simulación, presupuesto solver, umbrales realistas de tiempo, autorización del equipo sobre el protocolo y protección de datos.

## 15. Definition of Done de Fase 7

- [x] Protocolo experimental, familias, comparación, seeds, métricas, baseline, mitigaciones y 26 tests **especificados**.
- [x] Manifiesto de diseño de escenarios y contratos de resultados preparados.
- [x] Prompt para Codex redactado.
- [ ] F4 y F5 ejecutados y certificados por tests.
- [ ] Generador, fixtures y FIFO_FEASIBLE implementados.
- [ ] 48 pares experimentales ejecutados.
- [ ] Métricas/Metabase validados y análisis de resultados realizado.

**Conclusión:** esta fase está **completa a nivel de diseño experimental**. La ejecución pertenece a las fases de implementación posteriores. Nunca identificar resultados simulados con resultados de campo.
