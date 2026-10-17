# Fase 10 — Perfil sintético DEMO F4

Versión de implementación: `F4-DEMO-SYNTHETIC-1-REVIEW-PENDING`.
El usuario autorizó el 2026-10-17 proponer y versionar un perfil sintético **sólo para
`SIMULATED`**, sujeto a revisión. Los valores de este documento son supuestos de prueba;
no se atribuyen a especialistas ni son umbrales chilenos u operacionales. F4 sigue siendo la
fuente de las fórmulas.

| Parámetro | Valor DEMO | Unidad / interpretación |
|---|---:|---|
| R1 | 50 | lesiones graves por mil habitantes |
| R2 | 25 | personas atrapadas por mil habitantes |
| P_ref | 10 000 | personas afectadas |
| R5 | 2 | incremento relativo del tiempo de acceso |
| H_ref WATER, FOOD, SHELTER | 24 | horas por necesidad esencial |
| H_ref MEDICAL | 12 | horas por necesidad esencial |
| τ de antigüedad | 24 | horas por observación conocida |
| β salud, respuesta, coordinación | .50, .30, .20 | daño fraccional de cobertura de instalaciones críticas |
| α agua, electricidad, saneamiento, telecomunicaciones | .40, .25, .20, .15 | interrupción fraccional de población |
| q para cobertura C1…C7 | 1 cada uno | cobertura uniforme; `observed` sólo con respaldo utilizable |
| U incompletitud, antigüedad, conflicto | .50, .30, .20 | F4 §3, coeficientes DEMO |
| Pesos C1…C8 | .24, .12, .16, .12, .10, .10, .10, .06 | F4 §5, ilustrativos |

La matriz AHP DEMO se genera como `A_jk=w_j/w_k` para probar exactitud algebraica;
CR≈0 no implica acuerdo experto. La API selecciona exclusivamente este perfil en el
servidor, almacena su contenido y SHA-256 en cada corrida y valida `CR≤0.10` y `w8≤0.08`.
El perfil no se puede cambiar retroactivamente en una corrida.

## Contrato de observaciones para la demo

Los `metric_code` siguientes se capturan mediante reportes F9 con `source_id`,
`observed_at`, `recorded_at`, `evidence_status` y `unit`:

| Criterio | Códigos y unidades exactas | Regla |
|---|---|---|
| C1 | `severely_injured`, `trapped`: `persons` | F4 §3 con población basal >0 |
| C2 | `affected_people`: `persons` | logaritmo anclado en P_ref |
| C3 | `vulnerable_affected_unique`: `persons`; `affected_people` | personas únicas; V≤N |
| C4 | `health_damage`, `response_damage`, `coordination_damage`: `fraction` | β de cobertura; puentes y servicios básicos excluidos |
| C5 | `no_route_confirmed`: `boolean_0_1`; si vale 0, `actual_travel_sec`, `baseline_travel_sec`: `seconds` | ausencia de ruta sólo si dato `OBSERVED`; estimación o falta = desconocido; tiempos positivos |
| C6 | `water_interruption`, `electricity_interruption`, `sanitation_interruption`, `telecom_interruption`: `fraction` | α, suma 1 |
| C7 | necesidades esenciales `WATER`, `FOOD`, `MEDICAL`, `SHELTER`; `no_active_essential_need_confirmed`: `boolean_0_1` | F4 §3 y asistencia efectiva por necesidad |
| C8 | cobertura, antigüedad y discrepancias de observaciones comparables | F4 §3; sin comparación, conflicto 0 con bandera explícita |

`fraction` y `boolean_0_1` están en [0,1]; `persons` y `seconds` son no negativos;
`baseline_travel_sec` debe ser >0. La ausencia de un subindicador deja el criterio
correspondiente como `missing`, rango [0,1] y resultado exploratorio. Criterios conocidos
conservan valor, estatus y fuente; `NULL` nunca se convierte en cero observado. Las
estimaciones aprobadas conservan estado `estimated` y no cuentan como observadas en C8.

Sin una necesidad registrada ni confirmación explícita de ausencia de necesidad esencial,
C7 es `missing`, no cero. Una observación `OBSERVED` de
`no_active_essential_need_confirmed=1` permite C7=0. La cobertura completa de la única
necesidad esencial conocida también deja C7=0.

El usuario aprobó el 2026-10-17 para SIMULATED la regla D07: cada evento inmutable de
asistencia indica necesidad, cantidad, fecha efectiva y fuente. La base limita la suma
entregada a la cantidad declarada y rechaza fracciones de recursos discretos. En F4,
`f_ir=(quantity-delivered)/quantity`; una entrega parcial **no reinicia** el reloj de la
fracción pendiente, contado desde el inicio de la emergencia. La cobertura completa
elimina esa necesidad de C7. El evento no descuenta inventario, no reserva activos y no
equivale a aprobar una recomendación. Una necesidad sustituida con asistencia previa se
marca `assistance_supersession_unresolved` y C7 `missing` hasta conciliación explícita.

La demo selecciona el reporte utilizable más reciente por `observed_at`, luego
`recorded_at` e ID; los reportes sustituidos se excluyen. El conflicto normalizado entre
reportes vigentes del mismo fenómeno es el máximo de `(máximo−mínimo)/max(máximo,1)`,
recortado a [0,1]. Sin valores comparables, conflicto 0 y
`no_conflict_comparison=true`. Es una regla sintética de prueba, no una medida validada de
confiabilidad. La antigüedad es el promedio de `clip(age_hours/24)` entre observaciones
conocidas; sin ellas vale 1.

El usuario aprobó el 2026-10-17 para SIMULATED la regla D17: los empates de score dentro
de 1e-9 se agrupan respecto del mayor score del grupo y se
presentan por `zone_id` estable. Esta regla evita comparadores no transitivos; no modifica
ningún score.

La ruta `POST /api/v1/emergencies/{id}/priority-runs` acepta un snapshot previo de la misma
emergencia y encola el cálculo; `GET /api/v1/priority-runs/{id}/results` entrega puntaje,
intervalo, incertidumbre, factores y fuente. El worker sólo lee el snapshot inmutable y
el perfil versionado. Ninguna corrida genera cantidades de recursos, decisiones, reservas
u órdenes. Metabase sólo puede consultar las vistas `analytics.v_priority_results` y
`analytics.v_priority_factors`.

## Límites por revisar

- El traspaso de asistencia al sustituir una necesidad exige conciliación humana; la demo
  muestra C7 faltante y verificación en ese caso.
- Las métricas de acceso reportadas deben contrastarse con la red GIS y su vigencia
  antes de presentar una ruta como factible. El snapshot guarda `network_revision` y
  candidatos verificados; una contradicción entre `no_route_confirmed=1` y un candidato
  vigente deja C5 faltante, sube conflicto U y exige verificación. C5=1 no implica por sí
  solo bloqueo. La ausencia de candidato tampoco prueba aislamiento.
- Las definiciones de daño, conteos únicos, fuentes, conflicto y referencias necesitan
  evaluación de especialistas antes de cualquier uso institucional. La clasificación
  BAJA/MEDIA/ALTA/CRÍTICA es sólo una etiqueta ilustrativa.
