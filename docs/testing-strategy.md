# SIPRE — Estrategia de pruebas y validación

Fecha: 2026-10-16. Estado: **pruebas de implementación planificadas, no ejecutadas**. La comprobación de JSON/hashes y aritmética del ejemplo documentada en [architecture-review.md](architecture-review.md) no sustituye las pruebas aquí exigidas.

## Niveles, evidencia y puertas

| Nivel | Alcance / herramientas previstas | Evidencia | Momento |
|---|---|---|---|
| Unitario matemático | pytest, NumPy y fixtures F4/F5; casos frontera y propiedades deterministas | valores esperados, error absoluto, parámetros/versión | H5/H6 |
| Unitario simulación | FIFO, generador, KPI y exportación con fixtures de prueba/piloto | orden/plan, hashes, catálogo y NA | H11 |
| Contrato | DTO API, adaptadores IDs/estados/unidades, CSV/JSON | aceptación y errores tipados; no basta parsear JSON | H3/H11/H14 |
| Integración BD | PostgreSQL/PostGIS real con roles y migraciones | restricciones SQL, transacciones y consultas | H2–H12 |
| Seguridad | HTTPX/pytest, sesiones/CSRF/RBAC, credenciales SQL reales | accesos permitidos y denegados, ausencia de secretos | H4/H8/H10 |
| Concurrencia | dos o más conexiones/procesos y barreras de sincronización | decisiones/reservas resultantes y rollback | H8/H12 |
| Sistema/UI/BI | recorrido guiado portal + cinco dashboards; automatizar sólo flujos estables de alto valor | capturas, consulta SQL origen, logs y checklist | H9/H10/H12 |
| Rendimiento/recuperación | 10/30/100 zonas, estrés F7, reinicio worker/BD y restauración | p50/p95/RSS/hardware/versiones, fallos explícitos | H12 |
| Confirmatorio/exportación | validador independiente por plan y auditoría completa de pares | 48 fixtures, 96 ejecuciones, manifiestos/resultados | H13/H14 |

Cada ejecución de prueba registra comando, fecha, commit, locks/imágenes, ambiente, duración, resultado y artefacto. En F8 no hay commit ni suite. DoD por hito exige evidencia real y listado de pendientes. Las pruebas de seguridad/factibilidad no pueden omitirse por obtener H alto. No imponer un porcentaje de cobertura como sustituto de invariantes; medir cobertura y revisar ramas críticas no ejercitadas.

Pruebas en cada hito; H12 integra y audita, no espera al final para descubrir errores. H6 valida FIFO esperado de fixture y H11 vuelve a comprobarlo con baseline implementado. F7-03/20/24 se prueban inicialmente con enumeración/datos de prueba y se repiten sobre artefactos confirmatorios reales en H13/H14.

## Oráculos matemáticos y tolerancias

| Prueba/oráculo | Valor o propiedad exigida | Precaución |
|---|---|---|
| AHP consistente | matriz de razones de pesos demo → mismos pesos, CR≈0; RI8=1.41 | Matriz sintética no equivale a juicio experto; escala humana 1–9 por separado |
| Pesos/perfil | pesos positivos, suma dentro 1e-9; CR≤0.10; w8≤0.08 DEMO | Sin perfil válido → MODEL_NOT_CONFIGURED, no pesos uniformes inventados |
| TOPSIS F4 | Norte .778734, Rural .654473, Centro .548127; ranking Z01,Z03,Z02; tolerancia 1e-5 | Ideales fijos, sin normalización entre zonas |
| Extremos/propiedades | ceros→0, unos→1, monotonicidad, añadir zona no altera scores | Datos ausentes nunca se usan como ceros; ensayo de extremos usa datos observados |
| Incertidumbre | lower≤estimate≤upper con U fijo, flags por faltantes | Intervalo de sensibilidad, no IC; C8 y perfil congelados |
| Explicación | suma dplus_j=D+², suma dminus_j=D−² | Contrafactuales Δj no suman score |
| F5 fixture | SIPRE Norte 2/Rural 1; H=1.1059705; km=80; déficit 0/1 | Comparar agregados por zona; vehículo puede empatar según fixture |
| FIFO fixture | Rural 2/Norte 1; H=1.04384; km=80; cobertura física=.75 en ambos | Cola por tiempo/ID, no por score |
| F7 fixture | Hmax=1.433207; Hnorm FIFO=.7283246593129953 y SIPRE=.7716753406870047 | Δ=.04335068137400948; 4.3350681374 puntos porcentuales, no mejora física |
| Cobertura crítica fixture | FIFO=.5, SIPRE=1; sólo Z01 ≥.75 | Un ejemplo ilustrativo no es evidencia de efecto general |
| Lexicografía | H_final≥H_incumbente−εH; εH propuesto por F5=1e-8 | No confundir tolerancia de fixture 1e-6 con permiso de degradación H |

Tolerancias de capacidades, geometrías y decimales deben definirse por magnitud/unidad antes de H6/H11 y quedar en perfil. No recortar cantidades negativas/fraccionarias o violaciones del solver silenciosamente. Recalcular balance, H y costos desde el plan extraído; si incumple, no publicar como válido. Probar estados con solver real y también fallos controlados: los mocks verifican manejo de errores, no certifican matemática del backend.

## Validador de factibilidad común independiente

| Restricción F5 | Verificación desde plan y snapshot | Casos adversos mínimos |
|---|---|---|
| R01 | entregado + faltante = demanda conocida | q=0, q=NULL, cantidad excesiva o faltante negativo |
| R02 | suma por depósito/recurso ≤ stock libre del snapshot | dos vehículos compiten por últimas unidades |
| R03 | carga sólo si salida activada y combinación elegible | carga sin y, demanda no respaldada |
| R04 | una salida/destino por vehículo | dos destinos, reutilizar vehículo en otro ciclo comprometido |
| R05 | suma kg ≤ capacidad | mezcla de recursos con unidades distintas |
| R06 | suma m³ ≤ capacidad | peso admisible pero volumen excesivo |
| R07 | compatibilidad vehículo/recurso | refrigerado/no apto en MVP |
| R08 | ruta legal, disponible, vigente y T≤horizonte | BLOCKED, UNKNOWN, expiración, sentido/vuelta inexistente |
| R09 | unidad completa, única, cualificada, disponible, ruta válida | misión incompatible, equipo usado dos veces |
| R10 | unidades entregadas + faltante = demanda especializada | fracción o exceso de unidad |
| R11 | activación global por physical_asset_id ≤1 | ambulancia duplicada como transporte y unidad |
| R12 | misma emergencia/snapshot/versiones; finitos/unidades/integridad | mezcla entre emergencias, stock/red cambian |
| R13 | desconocidos fuera de asignaciones confirmables y visibles como verificación | imputación automática de litros desde TOPSIS |

El constructor MIP y el comprobador deben representar la misma especificación con cálculos independientes; compartir DTO y catálogo de unidades no implica reutilizar el resultado booleano del solver. FIFO pasa exactamente el mismo comprobador, sin privilegios menores ni excepciones.

## Casos técnicos complementarios (IDs de F8 propuestos)

| ID | Estímulo y aceptación | Hitos |
|---|---|---|
| T8-INF-01 | Compose limpio, build desde locks, imports/SCIP, health checks y reinicio con persistencia | H1/H12 |
| T8-DB-01 | Migraciones en BD vacía y actualización, FK por emergencia/CHECK/UNIQUE/NUMERIC/NULL; entrada inválida rechazada por SQL | H2 |
| T8-SNAP-01 | Escritura concurrente durante captura no produce snapshot híbrido; mismo contenido canónico produce mismo hash | H2/H3 |
| T8-AUTH-01 | Cada acción × rol × ámbito con permiso/denegación; ANALYST/ADMIN no heredan decisión, IDOR falla | H4/H8 |
| T8-AUTH-02 | CSRF ausente/incorrecto bloquea mutación; logout/revocación efectivos, contraseñas/cookies ausentes en logs | H4/H9 |
| T8-JOB-01 | Dos workers no publican dos resultados; lease vencido y reintento conservan intentos y dueño válido | H3/H12 |
| T8-IDEM-01 | Misma clave/cuerpo/actor no duplica; cuerpo distinto con clave reutilizada genera conflicto | H3/H8 |
| T8-GEO-01 | SRID/unidades/punto representativo correctos; grafo dirigido, restricciones y retorno verificados | H7 |
| T8-GEO-02 | Camino km-mínimo inválido no oculta alternativa admisible según política D18; mismos candidatos para métodos | H7/H11 |
| T8-CON-01 | Dos aprobaciones misma recomendación producen una decisión efectiva/reservas únicas | H8 |
| T8-CON-02 | Dos emergencias intentan mismo stock/activo: una espera/rechaza; saldo nunca negativo/activo solapado | H8 |
| T8-CON-03 | Cambio de red/inventario sincronizado con aceptación deja sólo resultado legal: éxito vigente o 409 sin reservas | H8 |
| T8-AUD-01 | Rechazo/aceptación/reoptimización reconstruibles; app no altera audit ni snapshots; rollback no deja decisión parcial | H8/H12 |
| T8-BI-01 | Rol BI SELECT sólo vistas permitidas; DML/DDL/base cruda fallan, DB de configuración persiste | H10/H12 |
| T8-BI-02 | Cinco dashboards concilian KPI con SQL; factores múltiples no multiplican stock, viajes o entregas; NA visible | H10/H14 |
| T8-REC-01 | Restaurar ambas bases y comprobar relaciones/hash/configuración BI; reiniciar worker no duplica plan | H12 |
| T8-RES-01 | Sin fuentes externas opera con snapshot almacenado y antigüedad visible; sin BD no acepta decisiones | H12 |
| T8-UI-01 | Flujo carga→prioridad→plan→revisión→aceptación con rol; teclado/labels/errores, SIMULATED e incertidumbre visibles | H9/H12 |
| T8-EXP-01 | Código planificador no puede abrir oracle ni recibe sus campos; alterar prioridad no cambia FIFO dado mismo input operativo | H11/H12 |
| T8-EXP-02 | Congelamiento rechaza hash/perfil/código distinto; 48 IDs únicos/96 métodos previstos; fallos conservados | H13 |
| T8-EXP-03 | Misma fixture resuelve evaluación H y KPI sin acceder a datos vivos; tiempos priority compartidos se contabilizan igual | H11/H13 |
| T8-EXPORT-01 | BD↔CSV↔JSON coincide por métrica/recurso/estado, NA vacío/null, hashes y nombres de catálogo estables | H11/H14 |

## Reproducibilidad y ejecución experimental

RNG fijado, `as_of_time` del fixture, canonicalización de JSON documentada (orden de claves/listas con semántica, decimales, Unicode, timestamps, rechazo de NaN/Infinity), IDs deterministas, software commit, locks/digests, versiones del solver y hardware. Comparar objetivos/cantidades conforme política de empates aprobada; no prometer identidad bit a bit entre hardware/backend distintos.

Un par utiliza exactamente el mismo snapshot, p y ω, restricciones y catálogo de rutas. Copias lógicas separadas impiden que el método ejecutado primero consuma inventario del segundo. Registrar tiempo de prioridad común y atribuirlo de igual forma al total de ambos pipelines, con tiempo de planificación separado; fijar política antes del confirmatorio. Orden de ejecución y calentamiento se preregistran antes de medir, no se ajustan mirando resultados. No crear resultados confirmatorios en F8.

Antes de H13 deben pasar F4/F5, validación de FIFO/generador/métricas, seguridad y auditoría; después se congelan y autorizan manifiestos. Conservar fallos/infeasible/no-solution y N efectivo por KPI; no convertirlos a cero. La evaluación valida factibilidad aunque no haya mejora de H. Publicar todos los 48 IDs y comprobar 96 ejecuciones efectivas; si faltan, no afirmar muestra completa.

## Comandos futuros propuestos (no ejecutados)

```text
docker compose config --quiet
docker compose build
docker compose up -d db
docker compose run --rm api python -m pip check
docker compose run --rm api alembic -c database/alembic.ini upgrade head
docker compose run --rm api python -m pytest backend/tests/unit -q
docker compose run --rm api python -m pytest backend/tests/integration backend/tests/contracts -q
docker compose run --rm api python -m pytest backend/tests/security backend/tests/concurrency -q
docker compose run --rm api python -m pytest backend/tests --junitxml=artifacts/tests.xml
```

Los nombres de servicios/rutas/configuración se confirmarán en H1. La suite usa base de pruebas y no genera ni ejecuta confirmatorios automáticamente. La futura CLI experimental se documenta al implementarla; no presentar un comando inexistente como disponible. No ejecutar `down -v` ni borrado de datos para preparar una demo con información existente.

## Catálogo obligatorio de aceptación de fuentes

Las tres tablas siguientes se transcriben de las especificaciones disponibles, conservando IDs y criterios. Son **71 pruebas especificadas: 17 F4 + 28 F5 + 26 F7**, no 71 pruebas ejecutadas o aprobadas. Hitos principales: P4→H5; P5→H6 con integración H7/H8/H11; F7→H11/H12 y comprobación final H13/H14.

### Fase 4 — Prioridad

Fuente: [SIPRE_PRIORIZACION_v1.md](../SIPRE_PRIORIZACION_v1.md). Estado de todos los casos: PENDIENTE DE IMPLEMENTACIÓN/EJECUCIÓN.

| ID | Prueba | Criterio de aceptación de la fuente |
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

### Fase 5 — Optimización

Fuente: [SIPRE_OPTIMIZACION_v1.md](../SIPRE_OPTIMIZACION_v1.md). Estado de todos los casos: PENDIENTE DE IMPLEMENTACIÓN/EJECUCIÓN.

| ID | Prueba | Criterio de aceptación de la fuente |
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

### Fase 7 — Experimentos

Fuente: [SIPRE_EXPERIMENTOS_v1.md](../SIPRE_EXPERIMENTOS_v1.md). Estado de todos los casos: PENDIENTE DE IMPLEMENTACIÓN/EJECUCIÓN.

| ID | Prueba | Criterio de aceptación de la fuente |
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
