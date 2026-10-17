# SIPRE — Fase 4: Especificación del modelo de priorización territorial

**Versión:** 1.0 — especificación de diseño, no validada operacionalmente  
**Proyecto:** Sistema de Priorización y Optimización de Recursos en Post-Emergencia (SIPRE)  
**Estado:** modelo formal propuesto; implementación reservada para fases posteriores  
**Stack previsto:** Python/FastAPI, PostgreSQL/PostGIS, OR-Tools (Fase 5), Metabase  
**Responsabilidad IA:** ChatGPT modela; Codex implementará posteriormente y ejecutará pruebas.  

## 0. Procedencia, propósito y alcance

Este documento desarrolla las Fases 2 y 3 establecidas en la conversación y las propuestas reportadas de la investigación de Gemini en PDF, especialmente: ocho criterios territoriales, AHP para pesos, TOPSIS para ranking, incertidumbre, tiempo de privación, explicabilidad y Human-in-the-Loop.

**Distinción importante:** la investigación de Gemini propone AHP-TOPSIS y los ocho criterios. Las reglas particulares de normalización, TOPSIS con referencias ancladas, ejemplos numéricos, umbrales de demostración y controles de seguridad definidos a continuación son **decisiones de diseño de este documento**, todavía no validadas con especialistas ni en terreno. Este motor no sustituye juicios clínicos, decisiones de rescate ni la autoridad del COGRID.

**Objetivo:** para cada zona territorial `zone_id` y emergencia `emergency_id`, calcular una prioridad explicable y reproducible a partir de 8 indicadores, diferenciando urgencia estimada, incertidumbre y necesidad de verificación. La asignación de vehículos/recursos y el ruteo corresponden a la Fase 5 y NO se implementan aquí.

## 1. Contrato de cálculo

Entradas mínimas:
- `emergency_id`, `zone_id`, `evaluated_at` con zona horaria, geometría referenciada y población basal.
- Observaciones por dimensión, incluyendo `value`, `unit`, `source_id`, `observed_at`, `recorded_at`, `status` (observado/estimado/desconocido), y valoración cualitativa de calidad cuando corresponda.
- `criteria_profile_version`: definiciones, valores de referencia, subpesos, unidades y sentido de cada variable.
- `ahp_profile_version`: matriz de comparaciones pareadas, pesos validados y criterio de consistencia.
- `classification_profile_version`: bandas ilustrativas/validadas y reglas de revisión.

Salidas obligatorias:
- `priority_score` (0–1, no probabilidad), `priority_rank` y `priority_level`;
- `criteria_values[8]`, `criteria_raw`, `weights[8]` y `factor_explanation`;
- `uncertainty_index`, `information_quality_flags`, `needs_verification`;
- `score_lower`, `score_upper` (intervalo de sensibilidad por datos faltantes, no intervalo de confianza estadístico);
- versión de datos, algoritmo, parámetros, timestamps y huella reproducible del escenario.

Invariantes: 0≤todo indicador≤1, 0≤score≤1, suma(pesos)=1 con tolerancia 1e-9, datos faltantes ≠ cero, reporte ≠ hecho corroborado, prioridad ≠ autorización de despacho.

## 2. Unidad de análisis y temporalidad

La unidad es una zona geográfica estable por emergencia (`zone_id`, geometría definida antes de calcular). Las observaciones pertenecen a `t_observado` y a la corrida `t_evaluacion`. Una corrida es instantánea y con snapshot de insumos: no puede cambiar mientras se calcula. Cambios posteriores generan una corrida nueva, no editan resultados históricos.

Se recomiendan cadencias de recálculo por evento significativo (nuevo dato, acceso modificado, recurso esencial entregado) y periódicas cuando se evalúe tiempo sin asistencia; la cadencia exacta es parámetro operativo, no se presupone conectividad en tiempo real.

## 3. Criterios y normalización anclada

Todos los criterios `Cj` se orientan como **mayor valor = mayor criticidad / necesidad de atención o de verificación**. `clip(x)=min(1,max(0,x))`. Valores de referencia y subpesos son configurables y versionados; no se recalculan usando el máximo de las zonas observadas, porque ello dificultaría comparar corridas en distintos momentos.

| Código | Criterio | Datos/subindicadores sugeridos | Normalización propuesta | Advertencias |
|---|---|---|---|---|
| C1 | Gravedad humana | personas gravemente lesionadas y atrapadas por mil habitantes | `0.65·clip((1000·severely_injured/P_base)/R1)+0.35·clip((1000·trapped/P_base)/R2)` | Umbrales R1/R2 requieren aprobación experta; C1 no es triaje individual. Si P_base o cifras faltan, dato desconocido. |
| C2 | Población afectada | N personas con necesidad conocida/estimada | `clip(log(1+N)/log(1+P_ref))` | P_ref fijo en el perfil, no máximo observado. No confundir población total con demanda confirmada. |
| C3 | Vulnerabilidad | afectados pertenecientes a grupos vulnerables únicos | `clip(V_afectados/max(N_afectados,1))` | Si N afectada es desconocida, C3 desconocido. Conteos agregados; evitar doble contabilización de personas. |
| C4 | Infraestructura crítica | impacto en servicios críticos que cubren la zona: salud, respuesta, coordinación | promedio ponderado de severidades de interrupción `Σ β_f·daño_f / Σ β_f` | Contabilizar **impacto de cobertura** aun si la instalación está fuera del polígono. Excluir puentes (C5) y cortes de servicios básicos (C6) para reducir duplicidades. |
| C5 | Accesibilidad | interrupción confirmada o aumento de tiempo de acceso | si se confirma ausencia de ruta: `1`; si hay ruta: `clip((T_actual/T_base −1)/R5)` | T_base>0, R5>0. Ruta desconocida ≠ bloqueada; registrar desconocido. |
| C6 | Servicios básicos | proporción de población sin agua, electricidad, saneamiento, telecomunicaciones | `Σ α_s·interrupción_s`, `Σα_s=1` | No asumir que sin registro el servicio funciona. Indicadores desconocidos se tratan como faltantes. |
| C7 | Tiempo sin asistencia | horas de necesidades esenciales sin cobertura efectiva | `max_{r en necesidades esenciales activas} clip(h_ir/H_ref,r)·f_ir` | `f_ir∈[0,1]` representa fracción de necesidad aún sin cubrir. Suministro parcial no debe reiniciar el reloj de toda la necesidad. Si no hay necesidades activas **confirmadas**, usar 0; si se desconoce, faltante. |
| C8 | Incertidumbre | incompletitud, antigüedad y contradicciones de reportes | `U=0.50·(1−coverage)+0.30·staleness+0.20·conflict` | Los coeficientes son **supuestos configurables para la demo**. U no representa peligro comprobado ni probabilidad. Debe mostrarse por separado. |

**Valores de referencia:** `R1`, `R2`, `P_ref`, `R5`, `H_ref,r` y pesos internos son parámetros externos con unidades, fuente, versión y fecha; no se prescriben como umbrales reales. Para pruebas sintéticas pueden recibir números arbitrarios **etiquetados claramente como DEMO**.

**C1:** en particular, gravemente lesionados/atrapados son números basados en reportes territoriales, no derivan del acelerómetro, IA ni triaje automatizado. El denominador censal debe >0 y la unidad debe ser homogénea.

**C7:** horas desde la última asistencia efectiva *por tipo de necesidad*, o desde el inicio del desastre si nunca existió asistencia y hay demanda conocida. No sumar aquí un costo de privación no validado. La Fase 5 tratará privación logística sin contabilizar dos veces el tiempo.

**C8 detallado:**
- `coverage = Σ_{j=1..7} q_j·observed_j / Σq_j`, donde `observed_j=1` sólo si Cj cuenta con un dato respaldado y utilizable. Valores imputados no cuentan como observados. `q_j>0` configurable; por defecto q_j=1.
- `staleness`: agregación ponderada del envejecimiento de reportes conocidos; por ejemplo, por componente `clip(age_hours/τ_j)` con τ_j establecido para cada fenómeno. Sin reportes, `staleness=1`.
- `conflict`: desacuerdo normalizado entre reportes sobre el mismo fenómeno, mediante regla y tolerancias documentadas; sin observaciones comparables, usar 0 **pero registrar ausencia de comparación**.
- `U` se reporta siempre de forma independiente de su participación en TOPSIS.

## 4. Tratamiento de información incompleta

No transformar `NULL` en 0. Para cada C1…C7 no conocido, conservar `status=missing`, rango admisible `[L_j,H_j]` (en ausencia de evidencia, `[0,1]`) y, sólo para un **resultado exploratorio**, un punto `c*_j=(L_j+H_j)/2`. Si existe una estimación justificada (por ejemplo preevento), usarla como `estimated` y conservar procedencia; nunca etiquetarla como observada.

El ranking operativo incluirá `score_estimate`, pero siempre irá acompañado de:
- `score_lower`: TOPSIS calculado con los límites inferiores de C1…C7 y C8 fijo;
- `score_upper`: TOPSIS calculado con límites superiores de C1…C7 y C8 fijo;
- `missing_criteria`, `needs_verification`, `high_uncertainty`.

Los límites representan **sensibilidad bajo valores admisibles**, no un intervalo de confianza al 95 %. La monotonicidad del TOPSIS anclado con indicadores 0–1 permite obtenerlos evaluando los extremos. Reglas conservadoras propuestas para MVP:
1. Si falta C1 o C5, `needs_verification=true` y queda prohibido presentar un ruteo hipotético como ruta confirmada.
2. Si faltan >=3 de los 7 criterios sustantivos, `needs_verification=true` (umbral de demostración, configurable).
3. Si U≥0.65, `high_uncertainty=true` (umbral de demostración, configurable).
4. Incertidumbre alta puede desencadenar **necesidad de reconocimiento/verificación**, pero nunca equivale por sí misma a autorización de envío de recursos.
5. Los criterios faltantes no deben reducir por defecto prioridad a 0; la UI muestra estimación, rango y etiqueta de confiabilidad.

## 5. AHP — Ponderación reproducible

Con 8 criterios, recibir una matriz A=(a_jk) 8×8, con a_jj=1, a_jk>0, a_jk=1/a_kj y juicios provenientes de una escala de importancia 1–9 (o sus recíprocos). El responsable del estudio de expertos y la metodología de obtención de estos juicios deberán constar en el expediente del proyecto. **No se pretende que la IA invente validación experta**.

Cálculo especificado del MVP (media geométrica de filas):

`g_j=(Π_{k=1}^8 a_jk)^(1/8)`

`w_j=g_j/Σg_j` con `Σw_j=1`.

Comprobación de consistencia:

`λ_max=(1/8)·Σ_j (A·w)_j/w_j`

`CI=(λ_max−8)/(8−1)`

`CR=CI/RI_8`, donde `RI_8=1.41` (valor clásico de referencia de Saaty).

**Regla MVP:** si `CR>0.10`, rechazar publicación de nueva versión de pesos y pedir revisar juicios; usar una versión ya aprobada si existe. Si `CR≤0.10`, se admite como consistentemente suficiente para pruebas **sin afirmar validación experta**. Guardar matriz, CR, aprobador y versión.

**Regla especial C8:** el peso de incertidumbre `w_8` deberá ser ≤0.08 en el perfil DEMO para evitar que ausencia de reportes domine necesidades documentadas. Si expertos justifican otra configuración, exigir revisión de gobernanza y sensibilidad. Este tope es una salvaguarda diseñada para el prototipo, no una constante científica.

**Pesos exclusivamente ilustrativos** (no definitivos, no validados):

| Criterio | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `w_demo` | .24 | .12 | .16 | .12 | .10 | .10 | .10 | .06 |

Para una prueba algebraica de consistencia exacta puede construirse una matriz `A_jk=w_demo,j/w_demo,k`, de la cual AHP retorna estos pesos y CR≈0. Tal matriz es **sintética de prueba**; no pretende representar juicios reales de expertos. Para entradas humanas se seguirá la escala de Saaty.

## 6. TOPSIS con ideal/antiideal de referencia fija

**Decisión de diseño:** usar TOPSIS *anclado a referencias 0 y 1*, en lugar de normalizar por el máximo/mínimo entre las zonas de una corrida. Motivo: un nuevo barrio no debería modificar artificialmente el puntaje absoluto de las zonas no modificadas. Es una variante de TOPSIS y debe identificarse como tal, no como TOPSIS canónico con normalización vectorial por alternativas.

Para cada zona i y criterio j: `c_ij∈[0,1]`. Todos los criterios están orientados como mayor criticidad; U es una señal informativa de peso limitado. Los pesos son `w_j>0`, `Σw_j=1`.

`v_ij=w_j·c_ij`

Ideal anclado: `v_j^+=w_j`.  Antiideal anclado: `v_j^-=0`.

`D_i^+=sqrt(Σ_j [w_j·(1−c_ij)]²)`

`D_i^−=sqrt(Σ_j [w_j·c_ij]²)`

`S_i=D_i^−/(D_i^++D_i^−)`.

El puntaje `S_i` está en `[0,1]`, donde mayor implica prioridad relativa respecto de las referencias fijas. No representa probabilidad de muerte, necesidad médica ni un estándar oficial. Calcular con precisión doble y guardar al menos 6 decimales; mostrar 2–3 decimales en Metabase.

**Orden:** prioridad descendente por `S_i`; empates numéricos con diferencia ≤1e-9 se resuelven por `zone_id` estable. El ranking debe identificarse por `model_run_id` y `as_of_time`. No clasificar como 'seguro' sólo porque S es bajo.

**Beneficio de la variante:** dado w_j positivos, si un único c_ij aumenta manteniendo los demás fijos, D^- no disminuye y D^+ no aumenta, por lo que S_i no disminuye. Además añadir zonas no modifica S_i de una zona previa.

**Atención:** no aplicar normalización adicional por máximo de zonas antes de calcular TOPSIS: destruiría el anclaje.

## 7. Bandas operacionales para demostración

Las bandas son **etiquetas del prototipo**, no umbrales oficiales ni certificados para operaciones reales:

- `0 ≤ S < 0.25`: BAJA
- `0.25 ≤ S < 0.50`: MEDIA
- `0.50 ≤ S < 0.75`: ALTA
- `0.75 ≤ S ≤ 1`: CRÍTICA

Una zona con `high_uncertainty=true`, `needs_verification=true` o una lesión grave documentada debe mostrar indicadores adicionales de revisión; no ocultarlos detrás de un color. Ningún umbral aislado debe originar un despacho automático.

## 8. Dinámica temporal y verificabilidad

En la corrida a tiempo t:
- recomputar C7 a partir de necesidades no cubiertas y horas desde última asistencia efectiva;
- recomputar C8 con edad/completitud/conflicto de información;
- recalcular c_i y S_i con parámetros de versión fija;
- guardar un snapshot inmutable de inputs, parámetros, score y factores.

Si transcurren 6 horas con los demás datos iguales, la variación de C7 (y eventualmente C8) puede aumentar S_i. Si llega información confiable, incertidumbre puede bajar aunque criticidad documentada suba: ambos fenómenos son válidos y deben explicarse.

El sistema no debe aumentar artificialmente urgencia por meras corridas repetidas: el tiempo transcurrido se calcula desde hechos, no desde la ejecución anterior.

## 9. Explicabilidad correcta de TOPSIS

No presentar como 'C1 aportó 24 puntos al resultado': TOPSIS **no es una suma lineal**. Entregar:
- vector C1…C8 normalizado;
- pesos y fuente de pesos;
- contribuciones a las distancias al ideal y antiideal: `dplus_j=(w_j·(1−c_ij))²`, `dminus_j=(w_j·c_ij)²`;
- análisis contrafactual `Δ_j=S(c)−S(c con Cj=0)` para **mostrar sensibilidad orientativa**, indicando que no es una descomposición aditiva y los Δ no suman S;
- criterios que más alejan/acercan a ideal;
- campos faltantes, intervalos de puntuación e incertidumbre.

La interfaz Metabase podrá mostrar factores, ranking e historia, pero la aprobación/modificación de recomendaciones deberá ejecutarse por una interfaz o API con permisos, no mediante una tarjeta BI que escriba en tablas operacionales.

## 10. Ejemplo sintético reproducible

Se utiliza `w_demo` y las ocho dimensiones **ya normalizadas**. Estos valores son inventados sólo para demostrar el algoritmo, no provienen del PDF ni representan daños reales:

| Zona | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Norte | .90 | .70 | .80 | .80 | .60 | .90 | .80 | .20 |
| Centro | .60 | .90 | .50 | .70 | .20 | .50 | .30 | .10 |
| Rural aislada | .55 | .35 | .90 | .60 | 1.00 | .80 | 1.00 | .90 |

Resultados esperados con TOPSIS anclado:

| Posición | Zona | D- | D+ | S | Banda demo |
|---:|---|---:|---:|---:|---|
| 1 | Norte | .312340 | .088747 | .778734 | CRÍTICA |
| 2 | Rural aislada | .272808 | .144028 | .654473 | ALTA; INCERTIDUMBRE ALTA |
| 3 | Centro | .222917 | .183772 | .548127 | ALTA |

En el ejemplo, C8 de Rural aislada=.90: la información deficiente debe ser visible y exigir verificación; **no es evidencia de daños reales**. Estos valores esperados se usarán como pruebas de regresión numérica con tolerancia razonable (`≤1e-5` para resultados redondeados).

## 11. Contratos de errores

- Matriz AHP no cuadrada/contiene 0/negativos/no recíproca: error validado, sin pesos nuevos.
- `CR>0.10`: matriz no aprobada (no sustituir automáticamente pesos con unos uniformes).
- Todos los pesos ausentes y ninguna versión previamente aprobada: estado `MODEL_NOT_CONFIGURED`.
- Todos los criterios sustantivos ausentes: generar estado `INSUFFICIENT_EVIDENCE`, verificación prioritaria y **no presentar ranking como una certeza**; permitir análisis de escenario exploratorio explícitamente rotulado.
- Datos por fuera de dominio (porcentaje >100%, timestamp futuro no explicado, demanda negativa): error de validación; no corregir silenciosamente.
- Zona inaccesible con ruta no verificada: no prometer ruta factible (ruteo pertenece a Fase 5).
- Datos de dos emergencias nunca deben mezclarse en la misma corrida.
- No permitir cambios retroactivos en parámetros de una corrida ya auditada.

## 12. Pruebas de aceptación obligatorias (Codex)

| ID | Prueba | Criterio de éxito |
|---|---|---|
| P4-T01 | Matriz de razón consistente | AHP reproduce pesos demo y CR≈0. |
| P4-T02 | Matriz con CR>0.10 | Rechaza publicación de perfil. |
| P4-T03 | Matriz asimétrica/0/negativa | Validación falla con mensaje útil. |
| P4-T04 | Entradas todos ceros/todos unos | S=0 / S=1 respectivamente. |
| P4-T05 | Ejemplo 3 zonas | Scores/ranking igual a §10, tolerancia 1e-5. |
| P4-T06 | Agregar una zona | Los scores absolutos de las zonas previas no cambian. |
| P4-T07 | Aumentar una sola criticidad | El score de esa zona no disminuye. |
| P4-T08 | Campo NULL vs 0 verdadero | NULL activa imputación marcada/intervalo; 0 permanece observado. |
| P4-T09 | Zona sin reportes | No recibe automáticamente S=0 y tiene bandera de verificación. |
| P4-T10 | Datos contradictorios/antiguos | U crece bajo regla de fuente/versiones constantes. |
| P4-T11 | Recalcular horas de privación | C7 responde a tiempo real transcurrido, no al número de ejecuciones. |
| P4-T12 | Análisis de sensibilidad por extremos | S_lower≤S_estimate≤S_upper (con U fijo). |
| P4-T13 | Prioridad vs explicación | D+ y D- se recomponen desde las contribuciones. |
| P4-T14 | Determinismo | Misma entrada/versión produce misma salida y orden. |
| P4-T15 | Separación de emergencias | Resultados no mezclan zonas de distintas emergencias. |
| P4-T16 | Configuración de pesos | Rechaza ausencia o pesos fuera del perfil aprobado. |
| P4-T17 | Ética/gobernanza | El motor no genera decisiones confirmadas ni órdenes de despacho. |

## 13. Sensibilidad y validación no ejecutada todavía

Diseñar y documentar ensayos de robustez:
- variación de pesos (p. ej., ±10% relativo en C1/C3/C5/C7 con renormalización y restricciones del perfil, no necesariamente cambios avalados por expertos);
- prueba de inversión de rankings al cambiar pesos y al variar criterios;
- intervalos con información faltante;
- perfiles de terremoto vs inundación sólo cuando existan matrices AHP justificadas;
- perturbación de tiempos sin asistencia y tasas de severidad;
- estabilidad entre corridas con igual perfil, comparabilidad de score.

Antes de uso institucional real se requeriría al menos evaluación con especialistas, validación de definiciones e indicadores, análisis de sesgos territoriales, ensayos retrospectivos y protocolo de respuesta ante datos deficientes. La validez del prototipo académico no implica certificación operacional.

## 14. Contrato para Fase 5

Entregar a Fase 5 por zona: `priority_score`, `priority_rank`, `factor_breakdown`, `uncertainty_index`, `score_lower/upper`, `needs_verification`, timestamp y versión, **además** de las necesidades por tipo de recurso y la demanda no atendida. Evitar usar indiscriminadamente `priority_score×costo_de_privación` si C7 ya representa tiempo sin asistencia: el siguiente modelo deberá demostrar cómo evita doble contabilizar el tiempo y cómo subordina distancias al objetivo humanitario.

TOPSIS no sustituye un cálculo de cantidades: una puntuación alta no determina cuántos litros de agua se necesitan ni cuántas ambulancias enviar.

## 15. Metabase: datos analíticos previstos

Se espera que la Fase 6 diseñe vistas SQL de solo lectura con columnas:

`emergency_id, zone_id, zone_name, run_id, evaluated_at, priority_score, priority_rank, priority_level, uncertainty_index, score_lower, score_upper, needs_verification, C1..C8, w1..w8, ahp_cr, profile_version, missing_criteria_count, observation_age_hours`.

Complementar con una tabla larga por factor (`run_id, zone_id, criterion_code, raw_value, normalized_value, weight, source, quality_flag, delta_counterfactual`) para mostrar evolución y explicabilidad de forma fácil en Metabase. Metabase no escribirá aprobaciones ni adjudicará órdenes.

## 16. Lista de pendientes/decisiones que requieren validación

- Validación experta de variables C1–C8 y subindicadores, especialmente definiciones de "grave" y vulnerabilidad.
- Números para R1, R2, P_ref, R5, H_ref por necesidad; justificación metodológica de cada valor.
- Estudio/panel AHP y pesos institucionales definitivos; el perfil demo NO es operativo.
- Reglas de agregación de discrepancias entre reportes, antigüedad aceptable por dato y fuentes confiables.
- Límite final de peso de C8 y umbrales de verificación.
- Detección/mitigación de doble conteo entre criterios y entre C7 y costo de privación de Fase 5.
- Criterios de clasificación por color, luego de pruebas de calibración.
- Qué situaciones requieren revisión humana reforzada o salida "datos insuficientes".
- Auditoría de sesgo hacia zonas con menor conectividad o menor representación censal.

## 17. Definition of Done (Fase 4)

- [x] Variables, unidades, normalización, orientación y datos faltantes especificados a nivel de diseño.
- [x] AHP, consistencia y reglas de versionado formalizados.
- [x] TOPSIS anclado con ecuaciones y muestra reproducible.
- [x] Incertidumbre, prioridad dinámica y explicabilidad definidas.
- [x] Contrato de entradas/salidas, fallos y pruebas especificado.
- [ ] Umbrales, subpesos y parámetros aprobados por expertos (pendiente de validación externa).
- [ ] Código y pruebas ejecutadas en repositorio (se realizará con Codex luego de Fases 5–8).

**Resultado:** modelo matemático especificado para implementación académica, no validado ni desplegado para decisiones reales.
