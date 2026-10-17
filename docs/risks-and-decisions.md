# SIPRE — Riesgos y decisiones de Fase 8

Fecha: 2026-10-16, America/Santiago. Estado: propuesta para aprobación humana. Ninguna decisión pendiente se considera aprobada por figurar aquí. Fuentes F4–F7 permanecen intactas.

**Estado actualizado al 2026-10-17:** este archivo conserva el historial de decisiones de F8;
las notas antiguas sobre falta de F2/F3, PostgreSQL, Docker o primer commit ya no describen el
repositorio actual. D01 y D24 quedaron resueltas con archivos y validaciones reales. El usuario
eligió explícitamente mantener sólo `SIMULATED` (C01). C02 (cuatro estados de emergencia) y C03
(`DECISION_MAKER` como nombre técnico de DECIDER) son refinamientos documentados, sin cambiar
F3/F6. D18 fue implementada y probada en H7, con revisión humana del hito aún pendiente.
Evidencia vigente: [cierre F9](phase9-closeout.md), [pruebas](phase9-test-evidence.md) y
[brechas](phase9-gap-analysis.md).

## Regla de autoridad

F4 rige priorización; F5, optimización; F6, arquitectura; F7, experimentación. La solicitud de F8 rige el alcance actual: sólo documentos. Ante conflicto entre dominios, registrar y aprobar una resolución versionada; no elegir silenciosamente una fórmula. Los identificadores D/R de este documento son de planificación, no requisitos oficiales del SRS.

## Contradicciones, vacíos y propuestas

| ID / severidad | Evidencia y problema | Información que falta / consecuencia | Solución propuesta, aprobación y puerta |
|---|---|---|---|
| D01 / bloqueante de trazabilidad | Faltan `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md`; README F7 confirma que no se exportaron | No se conocen los RF/RNF originales ni su aceptación; imposible certificar cobertura integral | Equipo aporta versiones aprobadas; cotejar y mapear IDs antes de H2. Puede autorizar H1 limitado a infraestructura y documentación sin presumir SRS completo |
| D02 / alta | F6 §16 aún marca arquitectura no ratificada; F4 mantiene parámetros DEMO sin validación experta | La aprobación del plan no equivale a validación institucional | Ratificar F8 y decisiones técnicas explícitas. Mantener DEMO/SIMULATED y validación experta fuera del cierre académico |
| D03 / bloqueante experimental | F7 §3 separa piloto; §8.7 propone elegir presupuesto usando E02-101, E03-101, E04-101, pertenecientes al confirmatorio | Selección de presupuesto puede usar evidencia reservada | Aprobar enmienda: seleccionar presupuesto sólo con piloto; conservar sensibilidad 101 después del confirmatorio como exploratoria, sin retocar principal. No aplicar hasta aprobación; conservar v1 original |
| D04 / alta | F5 ejemplo API: 30 s por etapa; F7 config: 15 s propuestos sin desglose | No está definido si 15 s son totales o por etapa, uso de incumbentes, hilos, tolerancias y gaps | En piloto definir presupuesto total y asignación a cada etapa, backend SCIP, semilla/hilos, política de incumbentes. H6 necesita perfil técnico; H13 exige perfil congelado aprobado |
| D05 / bloqueante del generador | F7 fija rangos, pero no distribuciones de demanda, topología, correlaciones, capacidades, cierres ni máscaras | Una semilla sola no define datos reproducibles ni distribución válida | Diseñar `experiment-generator.md`: RNG/versiones, subflujos por familia, distribuciones, redondeo, stock por recurso/depósito, tiempos, geometría, criterios, demanda desconocida y oracle. Aprobación antes de materializar confirmatorios en H13 |
| D06 / alta | F4 §3–5 y §16 deja R1/R2/P_ref/R5/H_ref, τ, discrepancias, subpesos y fuentes pendientes | No se puede ejecutar pipeline de reportes crudos con sólo el ejemplo normalizado | Aprobar perfil DEMO completo por parámetro, unidad y procedencia; sin números inventados. H5 puede probar núcleo sobre fixture normalizado, pero no cerrar pipeline sin perfil |
| D07 / alta | F4 C7 dice tiempo desde última asistencia efectiva y también prohíbe reiniciar por entrega parcial | Falta definición de evento efectivo, saldo y reloj por necesidad | Proponer ledger de asistencia por necesidad y reloj que preserve privación pendiente; aprobar semántica antes de C7/H5. No modificar fórmula C7 |
| D08 / alta | F6 enums `OBSERVED/ESTIMATED_APPROVED/UNKNOWN`; F5 fixture usa `CONFIRMED`; tabla API F6 usa `KNOWN/UNKNOWN` | Evidencia de observación, aprobación de demanda y conocimiento no son el mismo estado | Diccionario y adaptadores explícitos por tipo de entidad; aprobar quién valida estimaciones. H2/H3/H4; nunca mapear UNKNOWN a cero |
| D09 / media | F4/F5 fixtures usan Z01/E-DEMO y `KITS`; F6 exige UUID; F7 usa `KIT`; F5 demandas carecen de `request_id` | Importación y desempate FIFO no son directamente ejecutables | Mantener IDs externos y mapeo estable a UUID, alias KITS→KIT sólo en adaptador de fixture; derivación de request_id documentada y aprobada antes de H11; no editar originales |
| D10 / alta | F7 `RESULTADOS_SCHEMA` es catálogo descriptivo, no JSON Schema; sólo enumera parte de KPI | Validar sintaxis JSON no valida tipos, cardinalidades ni métricas; faltan catálogos y algunas unidades | Completar contratos tipados versionados, nombres canónicos y NA por métrica; F7 MD rige definiciones. Aprobación de normalización de nombres antes de H11 |
| D11 / alta | F7 usa `unmet_specialist` en texto y `unmet_specialized` en config; faltan `priority_runtime_ms`, memoria y cobertura mínima en catálogo JSON | Exportación puede perder indicadores o usar nombres incompatibles | Tabla de correspondencia exhaustiva y campos de dimensión para recurso/tipo/zona; sin inventar agregación de intervalos. Conservar requisito por zona y definir exportación antes de congelar |
| D12 / alta | F6 JSON `minimum_role` puede interpretarse como jerarquía; F6 §6 la niega explícitamente | ADMIN/ANALYST podrían recibir autorización de decisión indebidamente | Matriz por acción y alcance de emergencia, denegación por defecto. ADMIN no hereda decisión; sólo DECISION_MAKER asignado. Ratificación H4 |
| D13 / alta | F5 permite plan MODIFIED revalidado; F6 recomienda nueva corrida | Edición directa puede romper H, trazabilidad y factibilidad | Propuesta: modificación de insumos/restricciones crea nueva revisión y corrida; original queda histórica. Aprobar máquina de estados, cancelación/liberación de reservas y caducidades antes de H8 |
| D14 / alta | F6 entidades no detallan todas las FK por emergencia, reserva global ni versiones de vigencia | FK simple no impide mezclar zona de otra emergencia; carreras con cambios viales | FK compuestas donde corresponda, vínculos explícitos de activos compartidos, filas globales de revisión bloqueadas por todos los escritores; pruebas de concurrencia H2/H8 |
| D15 / alta | F6 §10 propone cola SQL, sin tabla completa ni recuperación de jobs | Reinicio puede duplicar resultados o perder trabajo aceptado | Worker del mismo monolito; cola PostgreSQL con claim atómico, lease/heartbeat, intentos y token de propietario; escritura final idempotente. No prometer ejecución exactamente una vez. Ratificar en H1, implementar H3 |
| D16 / alta | F5 εH=1e-8 condicionado al solver | Factibilidad interna del solver puede ser más laxa que conservación humanitaria | Recalcular H y R01–R13 con validador independiente; documentar tolerancia por magnitud. Si no cumple, no relajar en secreto: fallo/fallback permitido y aprobación del perfil H6 |
| D17 / media | F4 empate ≤1e-9 no define agrupación; F5 P5-T22 pide mismas cantidades, aunque puede haber varios óptimos | Comparador por cercanía puede ser no transitivo; ordenar presentación no vuelve único un óptimo | Documentar agrupación estable para F4 y política reproducible de empates para solver; aprobar antes de cerrar H5/H6. Comparar agregados sólo donde fixture lo permite; no añadir tercer objetivo sin autorización |
| D18 / alta | F5 rutas factibles, F6 NetworkX; sin selección exacta de candidatos | Camino más corto en km puede exceder horizonte existiendo otro válido más rápido; faltan restricciones por vehículo | Aprobar política de candidatos sobre grafo dirigido, vuelta, descarga y restricciones; no declarar inalcanzable usando sólo un camino inviable. Mismo catálogo para ambos métodos; H7 antes de H6. **2026-10-17:** implementada en H7 como decisión operativa (Dijkstra por tiempo de viaje con elegibilidad por vehículo y horizonte); sigue pendiente ratificación formal |
| D19 / media | F4 ejemplo Rural tiene C5=1; F5 esa zona sí tiene ruta | C5=1 puede significar retraso saturado o aislamiento, no prueba unívoca de bloqueo; fixture F5 sólo reutiliza scores | Mantener fixtures por dominio, no inferir ruta de C5. Pipeline integrado debe derivar C5 y rutas del mismo snapshot y documentar procedencia |
| D20 / media | F5 propone nombres `vw_*`; F6 define doce vistas `analytics.v_*` | Posible duplicación BI y falta de campos F7 | Adoptar catálogo F6 y ampliar campos experimentales F7 mediante migración; mapear conceptos F5, sin segundo dashboard |
| D21 / media | F7 piloto: una instancia por familia con semillas 1–4, sin correspondencia explícita | Puede interpretarse como 4 o 16 pilotos | Proponer E01-1, E02-2, E03-3, E04-4: cuatro pilotos. Ratificar antes de H11; no afecta 48 confirmatorios |
| D22 / alta | F7 §8 pide controles con H fijado por referencia §6.1, sin diseño completo | No está fijado conjunto de controles ni tolerancia de comparación logística | Diseñar y aprobar controles exploratorios antes de ejecutarlos; separar de los 96 principales. No inferir eficiencia de Δkm cuando H cambia |
| D23 / resuelta en F9 | Usuario aportó pauta con cuatro categorías y quince ítems, total 90 | No se asignan pesos individuales ni se presupone otra categoría | Pauta incorporada en evaluation-rubric.md el 2026-10-16; conservar total 90 y evaluar con evidencia, sin puntajes autoasignados |
| D24 / alta | Sin Python instalado reconocido por launcher; Docker no localizado en PATH/rutas habituales | No se ha demostrado despliegue ni compatibilidad binaria | H1 debe verificar/provisionar entorno autorizado y ejecutar smoke checks. No instalar durante F8 |
| D25 / media | OPEN-01 F6: PDF Gemini no presente; no hay actas expertas ni datos operacionales | No se puede verificar atribución de investigación ni validación externa | Conseguir referencias si son necesarias para informe; no bloquear motor DEMO por validación real fuera de alcance |

## Riesgos técnicos y mitigación verificable

| ID | Probabilidad / impacto | Mitigación | Evidencia de cierre / responsable propuesto |
|---|---|---|---|
| R01 | Alta / alto: alcance sin SRS | D01 y trazabilidad provisional explícita | SRS firmado y matriz revisada; equipo |
| R02 | Media / crítico: doble reserva | Locks globales, idempotencia, transacción de decisión y reservas | Pruebas de carreras H8; backend |
| R03 | Media / crítico: ruta obsoleta | Revisión de red bloqueada al confirmar y caducidad | Cambio concurrente invalida plan; GIS/backend |
| R04 | Media / alto: contaminación experimental | D03, separación piloto/oracle, hashes y congelamiento | Manifiesto y pruebas F7-01/02/21; responsable experimental |
| R05 | Media / alto: numerics/timeout | MIP mixto, validador independiente, estados por etapa | P5-T18/19/20 y benchmarks; optimización |
| R06 | Alta / medio: memoria local/Metabase JVM | Un worker, cola secuencial, presupuesto medido, limitar concurrencia | p50/p95/RSS y restauración local; infraestructura |
| R07 | Media / alto: credenciales BI excesivas | Roles SQL separados, vistas curadas, DB Metabase separada | SELECT permitido; DML/DDL/tablas crudas denegados; seguridad |
| R08 | Alta / alto: sesgo hacia zonas con datos | Intervalos, flags, oracle sólo evaluación, déficit por zona | F4/F7 y dashboard con zonas desconocidas; equipo |
| R09 | Media / alto: deriva de dependencias | Pins/hashes/digests, prueba binaria limpia, registro de backend | Entorno reproducible H1/H12; infraestructura |
| R10 | Media / alto: resultados parciales publicados como válidos | Manifiesto de intención con 48 IDs, 96 estados, NA y exclusiones | F7-19/20/24; responsable experimental |
| R11 | Media / alto: auditoría incompleta | Append-only por aplicación/SQL y backup con restauración | Decisión reconstruible, no prometer inmunidad al DBA; backend |
| R12 | Alta / medio: plazos universitarios | Núcleo de una parada, UI ligera, sin servicios extra | Entregas autorizadas por hito, extras fuera del camino crítico; equipo |

## Registro de aprobaciones

Estado inicial de D01–D25: ABIERTO (las propuestas no constituyen cambios en las fuentes). Registrar al resolver: ID, alternativa aceptada, motivo, aprobador, fecha, versiones/hashes afectados, hitos desbloqueados y pruebas requeridas. No cerrar por paso del tiempo ni por falta de respuesta.

Registro histórico F9, 2026-10-16: usuario autorizó continuar Fase 9 y entregó pauta (D23 resuelta). A la consulta por SRS/formulación respondió «Aportaré la formulación y el SRS»; en ese momento D01 seguía abierta y el trabajo se limitaba a infraestructura. Python 3.12.14 estaba disponible, pero Docker/PostgreSQL aún no habían sido validados. Este estado fue superado por la evidencia del 2026-10-17 indicada al inicio del documento.

Primera aprobación solicitada: plan F8 y alcance de H1; monolito/UI ligera/worker SQL/stack candidato; obtener F2/F3 y pauta o autorizar explícitamente H1 limitado mientras se aportan. D03 y D05 bloquean confirmatorio, no el trabajo documental ni la infraestructura inicial. Cada siguiente hito necesita nueva autorización explícita del usuario.


## Actualización de auditoría F9 — 2026-10-16

F2 y F3 ya están disponibles como `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md` en la raíz y fueron revisados completos. Las referencias anteriores a su ausencia describen el estado previo. En esa auditoría histórica, Fase 9 permanecía **BLOCKED** por infraestructura sin validación online y H2–H4 incompletos. Posteriormente se implementaron y verificaron; dictamen vigente: [phase9-closeout.md](phase9-closeout.md).

