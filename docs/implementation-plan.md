# SIPRE — Plan integral de implementación

Fecha: 2026-10-16. Versión: phase8-plan-v1. Estado: planificación terminada para revisión; implementación no autorizada ni iniciada. Regla: **SIPRE recomienda; la autoridad humana decide**.

## Alcance, fuentes y puertas

Se implementará el prototipo académico F4–F7: AHP geométrico, TOPSIS anclado, incertidumbre y C7, MIP lexicográfico con R01–R13, una salida y un destino por vehículo, GIS de escenario, decisiones separadas, Metabase lector y experimento FIFO_FEASIBLE/SIPRE. No se altera modelo, requisitos, muestras o métrica para favorecer resultados. F2/F3 faltan y la trazabilidad es provisional; ver [revisión](architecture-review.md), [decisiones](risks-and-decisions.md) y [matriz](requirements-traceability.md).

Hito se abre sólo con autorización explícita del usuario. Al terminar, entregar archivos/diff, comandos y resultados reales, pruebas no ejecutadas, riesgos y criterio DoD; **detenerse antes del siguiente hito**. Un test planificado no cuenta como aprobado. No efectuar automáticamente commits, publicación o cambios de alcance por dar por aprobado el roadmap.

Orden propuesto: **H1 → H2 → H3 → H4 → H7 → H5 → H6 → H8 → H9 → H10 → H11 → H12 → H13 → H14**. Se conserva numeración solicitada. Adelantar H7 garantiza datos GIS/C5 y rutas legales antes de priorización integrada/optimización. Los núcleos F4/F5 se prueban con fixtures ya disponibles en sus hitos; no se difieren todas las pruebas a H12. H10 entrega vistas/dashboard con datos sintéticos de prueba y H11 añade los campos/métricas experimentales, revalidados en H12.

Las fases F9–F16 mencionadas en F6 son agrupaciones históricas, no estos hitos: F9≈H1–H4; F10≈H5; F11≈H6/H8; F12≈H7; F13≈H11; F14≈H10; F15≈H12; F16≈H13–H14.

## Hito 1 — Inicialización e infraestructura

- **Objetivo:** disponer de base reproducible local sin reglas de negocio implementadas.
- **Dependencias/entrada:** aprobación F8/H1, D02/D15/D24; confirmar directorio como repo nuevo o aportar checkout real. D01 admite sólo excepción explícita para infraestructura mientras llegan F2/F3.
- **Archivos/módulos:** README, `.gitignore`, `.env.example`, `pyproject.toml`, locks, `compose.yaml`, `docker/`, esqueleto de paquete y tests, documentación de instalación.
- **Requisitos relacionados:** TR-01, TR-19, TR-20; F6 ADR-001/004/012 y §10–12.
- **Actividades:** inicializar Git sólo tras autorización; preservar fuentes/hash; seleccionar versiones/digests; imágenes API/worker comunes; PostgreSQL/PostGIS y dos DB separadas; secretos fuera de repo; puertos localhost, volúmenes, health checks y servicio de migración. Esqueleto no incorpora cálculos o decisiones.
- **Pruebas:** configuración Compose válida, build/imports y `pip check`, disponibilidad SCIP mixta, readiness de servicios, persistencia tras reinicio; no usar volúmenes con datos valiosos para prueba.
- **Entregables:** entorno base, instrucciones Windows/Linux, versiones efectivas y evidencia smoke, incidencias pendientes.
- **Riesgos:** Docker/Python no disponibles actualmente, arquitectura CPU/wheels, memoria JVM; no resolver con servicios comerciales por defecto.
- **Definition of Done:** todos los archivos iniciales revisados, arranque reproducido desde locks/digests, secretos ausentes, sin implementación matemática.
- **Aceptación:** equipo puede repetir pasos documentados en host autorizado y reiniciar conservando datos de prueba; falla si el stack sólo funciona por dependencias globales ocultas.

## Hito 2 — PostgreSQL/PostGIS, modelo y migraciones

- **Objetivo:** materializar contratos de integridad, versionado y almacenamiento F6.
- **Dependencias/entrada:** H1 aceptado; F2/F3 aportados y diferencias resueltas; D08/D09/D14 definidos, capacidades preliminares y política de unidades aprobadas.
- **Archivos/módulos:** `database/migrations/`, `database/bootstrap/`, `backend/app/db/`, `domain/`; esquemas core/ops/geo/model/planning/audit/experiments/analytics.
- **Requisitos:** TR-02–05, TR-08, TR-13–15; F6 §4/7.
- **Actividades:** entidades/constraints F6, UUID/IDs externos, timestamps UTC, NUMERIC para cantidades, perfiles/snapshots inmutables, factores completos, ledger/reservas globales; FK por emergencia; índices GiST y de consultas; roles SQL mínimos. Migraciones para jobs/sesiones e idempotencia técnicas propuestas. `metabase_app` no recibe tablas de dominio.
- **Pruebas:** BD nueva → migración head; actualización desde revisión anterior de prueba; negativos/NaN/entero/unidades/NULL/FK inválidas rechazados; aislamiento de emergencias, ledger, geometrías y roles; backup/restore de prueba sin pérdida.
- **Entregables:** esquema migrado, diagrama actualizado, diccionario de datos y pruebas BD.
- **Riesgos:** FK aisladas insuficientes, reservas descontadas dos veces, modificar perfiles usados.
- **Definition of Done:** invariantes expresables respaldadas en SQL, migraciones repetibles y transacciones documentadas, no sólo validadores Python.
- **Aceptación:** datos inválidos se rechazan vía API futura o SQL directo del rol aplicativo; snapshots/resultados/audit no admiten actualización normal; stock libre reconstruible.

## Hito 3 — Backend FastAPI, contratos y API

- **Objetivo:** casos de uso CRUD/versionado e infraestructura de ejecución asíncrona segura.
- **Dependencias:** H2; D08–D10/D15 resueltos para contratos. Hasta H4, endpoints mutantes no se habilitan a usuarios externos; sólo tests locales aislados con dependencias de autenticación simuladas explícitamente.
- **Archivos/módulos:** `api/v1/`, `application/`, módulos de datos, `jobs/`, `settings.py`, contratos y errores.
- **Requisitos:** TR-02–05, TR-13, TR-20; endpoints y errores F6 §6.
- **Actividades:** validación tipada, paginación, límites de importación, fuente/unidad/offset, errores útiles, idempotencia y correlación; snapshots atómicos; cola SQL 202, polling, lease, reintentos y persistencia final idempotente; motores aún no disponibles deben responder estado explícito, no éxito ficticio.
- **Pruebas:** contratos, 422 por inválidos, 409 por revisiones/clave incompatible, fechas sin offset, mezcla de emergencias, duplicate POST; caída/reclamación del worker y token vencido sin doble publicación.
- **Entregables:** OpenAPI real, ejemplos request/response, API local, worker y tests.
- **Riesgos:** CPU solver bloqueando HTTP, claim de job no durable, exposición prematura de mutaciones.
- **Definition of Done:** cada endpoint implementado tiene contrato y prueba de errores; cola persiste y no publica duplicados; no anuncia motor implementado antes de H5/H6.
- **Aceptación:** repetir solicitud no duplica operación; ID 202 permite consultar estado verdadero; pérdida de proceso conserva trabajo rastreable.

## Hito 4 — Autenticación, roles y seguridad

- **Objetivo:** autorización explícita por acción y emergencia, segregación humana/BI.
- **Dependencias:** H3; aprobación D08/D12, política de sesiones y responsable de estimaciones.
- **Archivos/módulos:** `auth/`, dependencias API, sesiones/migraciones, `audit/`, tests de seguridad.
- **Requisitos:** TR-14, TR-15, TR-18, TR-20; F6 §9.
- **Actividades:** sesiones servidor, hash Argon2id, cookies, CSRF, expiración/revocación; capacidades ADMIN/OPERATOR/ANALYST/DECISION_MAKER/VIEWER sin herencia; pertenencia a emergencia, login/logout/me; rate limit local, CORS, redacción de logs y cuentas iniciales sin contraseña embebida.
- **Pruebas:** 401/403 y denegación transversal, IDOR otra emergencia, VIEWER no escribe, ANALYST/ADMIN sin capacidad no aprueban, CSRF/cookie/logs, cierre de sesión y revocación, secretos ausentes.
- **Entregables:** matriz de permisos, autenticación funcional y pruebas negativas.
- **Riesgos:** interpretar `minimum_role` como orden, autorización sólo en navegador.
- **Definition of Done:** cada mutación verifica capacidad en servidor y deja evento; usuario Metabase y usuario API son separados.
- **Aceptación:** ninguna ruta alternativa (API/UI/job) evade control; prueba por cada capacidad/rol y ámbito autorizado/no autorizado.

## Hito 5 — Priorización AHP-TOPSIS

- **Objetivo:** motor puro completo F4 e integración persistente explicable.
- **Dependencias:** H4 y H7 en orden propuesto; D06/D07/D17 resueltos; perfil DEMO aprobado, sin fingir validación experta.
- **Archivos/módulos:** `prioritization/ahp`, criterios/uncertainty/topsis/explanation, `profiles/`, API/jobs, tests F4.
- **Requisitos:** TR-06–09; F4 §§1–12.
- **Actividades:** ocho criterios anclados, AHP geométrico, RI8=1.41, CR≤0.10, w8≤0.08 DEMO; score e intervalos U fijo; NULL/estimated/observed; C7 por hechos y C8 por antigüedad; dplus/dminus y contrafactual no aditivo; versiones/errores y orden estable.
- **Pruebas:** P4-T01…P4-T17, extremos, propiedades monotónicas, invariancia al agregar zonas, explicaciones y separación de emergencias; fixture a tolerancia 1e-5.
- **Entregables:** motor, 17 casos fuente implementados, perfil aprobado y resultados persistidos.
- **Riesgos:** rellenar referencias faltantes, doble conteo temporal, scores como probabilidades, empates no transitivos.
- **Definition of Done:** toda salida reconstruible desde snapshot/perfiles; publicación rechaza CR inválido o perfil ausente; U visible.
- **Aceptación:** fixture produce Z01>Z03>Z02; NULL nunca equivale a cero; corrida no crea decisión ni cantidades de demanda.

## Hito 6 — Optimización OR-Tools

- **Objetivo:** asignaciones mixtas factibles, objetivo H primario y km secundario.
- **Dependencias:** H5 y H7, perfiles/logística y D04/D16/D17 aprobados; stock, flota, rutas y prioridades del mismo snapshot.
- **Archivos/módulos:** `optimization/`, `planning/feasibility`, `planning/evaluation`, jobs/API/repositorios, pruebas F5.
- **Requisitos:** TR-10–13; F5 R01–R13, §§6–11.
- **Actividades:** variables x/y/z/h/g, kg/m³, enteros/continuas, activos compartidos; maximizar H, luego minimizar C con H≥incumbente−ε; registrar backend/cotas/gaps/tiempos; extraer plan y validarlo externamente; faltantes conocidos/UNKNOWN separados, reserva sólo en H8.
- **Pruebas:** P5-T01…P5-T28, verificaciones físicas y fallos controlados; P5-T02 se valida contra asignación FIFO de referencia ahora y contra implementación FIFO en H11; H*=1.1059705, km=80 en fixture.
- **Entregables:** solver versionado, evaluador/validador compartidos, errores/estatus y evidencia de conservación lexicográfica.
- **Riesgos:** tolerancia mayor que diferencias relevantes, plan sin rutas, timeout disfrazado, simetrías, una parada confundida con CVRP.
- **Definition of Done:** cada plan publicado pasa verificador independiente; estado solver separado de validez y decisión; P5-T02 queda integrada nuevamente con baseline real en H11/H12.
- **Aceptación:** no exceder stock/capacidades, no fraccionar bienes discretos/unidades, no rutas no elegibles; etapa 2 falla según fallback F5 sin fabricar solución.

## Hito 7 — GIS, rutas y bloqueos (se ejecuta antes de H5/H6)

- **Estado (2026-10-17):** implementado, `READY_FOR_REVIEW`; pendiente de aprobación humana. Evidencia: suite local 51 pruebas en verde (unit + integración con PostGIS), ruff limpio, migración `0005_gis_network` con triggers de revisión/invalidación/guard/auditoría; Docker/E2E no re-ejecutables en este entorno (`wsl.exe` ausente del PATH). D18 aplicada como política operativa sin ratificación formal.
- **Objetivo:** preparar accesibilidad y rutas verificadas dentro del escenario.
- **Dependencias:** H4, D18 y caducidades técnicas aprobadas; red sintética de pruebas (no confirmatoria).
- **Archivos/módulos:** `gis/`, `transport/`, `zones/`, tablas geo, migraciones y tests GIS.
- **Requisitos:** TR-03, TR-09, TR-12; F6 §5 y F5 R08/R09/R12.
- **Actividades:** validación SRID 4326, medición métrica/geography, punto dentro de polígono; grafo dirigido con restricciones por clase de vehículo, rutas ida/vuelta y descarga, secuencia de arcos/revisión/expiración; bloquear UNKNOWN/BLOCKED; invalidación de candidatos y, cuando exista H8, recomendaciones dependientes.
- **Pruebas:** arco cerrado, sentido único, vuelta inexistente, ruta restringida por vehículo, caducidad, geometría inválida y unidad métrica; caso camino corto lento frente a alternativa válida conforme política D18.
- **Entregables:** proveedor común de rutas y C5, catálogo versionado, eventos de invalidación y pruebas; integración completa STALE se cierra H8.
- **Riesgos:** tratar OSM como evidencia operacional, grados como metros, confundir score C5 con ruta confirmada.
- **Definition of Done:** candidatos reproducibles y con trazado por arcos; elegibilidad explícita por vehículo/unidad y horizonte.
- **Aceptación:** ninguna ruta retornada para planificación cruza bloqueos/desconocidos ni incumple restricciones; ausencia de ruta se reporta sin inventar modo aéreo.

## Hito 8 — Recomendaciones, aprobación y auditoría

- **Objetivo:** separación verificable entre resultado del software y decisión humana.
- **Dependencias:** H6/H7/H4; D13/D14, expiración, liberación de reservas y máquina de estados aprobados.
- **Archivos/módulos:** `recommendations/`, `application/decisions`, reservas, `audit/`, tests de concurrencia.
- **Requisitos:** TR-13–15; F6 §§3/6.3/7, F5 §10.
- **Actividades:** revisión/rechazo/aceptación/reoptimización; lock y comparación de todas revisiones, identidad del servidor, validación física y vigencia, transacción única decisión+reservas+audit; conservación histórica; nueva corrida al modificar plan.
- **Pruebas:** aprobación idempotente, dos decisiones simultáneas misma recomendación, mismo stock/activo entre emergencias, cambio de red/stock mientras se confirma, rollback completo, 403, caducidad y trazabilidad.
- **Entregables:** flujo transaccional completo y bitácora reconstruible.
- **Riesgos:** reserva parcial, autor falsificado, versión revisada sin lock, inventario global inconsistente.
- **Definition of Done:** todas las carreras críticas controladas con BD real; no hay ruta software de despacho externo.
- **Aceptación:** recomendación sola no cambia stock; cambio relevante produce 409 STALE sin reserva; aceptación deja decisión humana separada y no orden operacional.

## Hito 9 — Interfaz operacional mínima

- **Objetivo:** permitir cargar datos, solicitar corridas y revisar/decidir con contexto.
- **Dependencias:** H8, ratificación Jinja2/HTMX y capacidades H4.
- **Archivos/módulos:** `ui/templates/`, `ui/static/`, formularios y rutas backend.
- **Requisitos:** TR-02, TR-08, TR-14, TR-16; F6 ADR-005.
- **Actividades:** formularios por rol, tablas de insumos/errores, ejecución y estado de jobs, explicación e intervalos, detalle de rutas/déficits y acción humana explícita; banner SIMULATED, manejo de versiones stale; enlaces a Metabase para análisis.
- **Pruebas:** recorrido por cada rol, navegación teclado/etiquetas/errores legibles, CSRF/XSS y acciones no autorizadas, refresh de job, no doble submit.
- **Entregables:** portal funcional, guía corta y capturas de aceptación.
- **Riesgos:** aprobación implícita al generar, ocultar incertidumbre con color, duplicar BI.
- **Definition of Done:** operación esencial completa sin consola SQL; no pantalla analítica paralela.
- **Aceptación:** operador/analista/decisor ejecutan sus acciones permitidas, incertidumbre y carácter recomendado son visibles antes de aceptar.

## Hito 10 — Metabase y dashboards

- **Objetivo:** BI exclusivo sobre vistas SQL controladas.
- **Dependencias:** H8/H9, doce vistas F6; enriquecimiento experimental de H11 pendiente explícito.
- **Archivos/módulos:** `database/views/analytics/`, migraciones, `metabase/dashboards.md`, evidencias.
- **Requisitos:** TR-17–18; F6 §8 y F7 §10.
- **Actividades:** rol `sipre_metabase_reader`, DB de configuración separada, cinco dashboards situación/priorización/recursos/logística/experimentos; filtros por emergencia/run/familia/seed, marcadores lat/lon, NA/flags/refresh/versiones; preguntas/consultas documentadas y backup DB Metabase.
- **Pruebas:** consulta correcta por granularidad, no multiplicar cantidades al unir factores/asignaciones, lector sin DML/DDL/tablas crudas; UI visible SIMULATED; persistencia tras reinicio. Comparativo inicial usa fixture ilustrativo, sin resultados confirmatorios.
- **Entregables:** cinco dashboards, doce vistas y procedimiento de reconstrucción/restauración.
- **Riesgos:** permisos sólo cosméticos, cache presentado como tiempo real, contar viaje una vez por recurso.
- **Definition of Done:** lecturas verificadas contra datos base, seguridad probada con credencial real; catálogo listo para extensión F7 en H11.
- **Aceptación:** no hay acción de escritura operacional; captura y prueba SQL de cada dashboard/permiso; mapa básico sin prometer polígonos dinámicos.

## Hito 11 — Generador, FIFO_FEASIBLE y métricas

- **Objetivo:** pipeline experimental reproducible, aún sin cohortes confirmatorias materializadas.
- **Dependencias:** H5/H6/H7/H10; resolver D03–D11/D21/D22 según aplique; aprobar contrato de generación antes de congelamiento.
- **Archivos/módulos:** `experiments/generator`, `baseline_fifo`, `metrics`, `pipeline`, `exports`, config/piloto/oracle, migraciones y vistas F7, documentación generador/ejecución.
- **Requisitos:** TR-21–25; F7 §§3–12 y F5 §13.
- **Actividades:** RNG/versiones y bytes canónicos; generador de prueba/piloto E01–E04; aislamiento oracle; FIFO orden UTC/request_id, selección costo/IDs, carga residual sólo misma zona, unidades completas; validador/evaluador comunes; KPI con NA, unidades y manifiestos; persistencia de métodos sin reservar inventario compartido.
- **Pruebas:** F7-01…26 aplicables a piloto/fixtures, P5-T02 con FIFO real, determinismo e independencia de prioridad al asignar, oracle inaccesible, métricas F7 de ejemplo; contrato de enumeración 48 IDs sin generar fixtures definitivos.
- **Entregables:** software generador/baseline/evaluador, catálogo completo, documentación y piloto reproducible, dashboard experimental actualizado.
- **Riesgos:** calibración para favorecer H, fuga oracle, distribución no aprobada, parámetros distintos entre métodos.
- **Definition of Done:** componentes listos y probados con datos de prueba/piloto; cada parámetro tiene dueño/versión; cohorte confirmatoria reservada a H13.
- **Aceptación:** ambos métodos consumen mismo snapshot y producen planes válidos evaluados igual; piloto excluido de N=48; no generar datos finales anticipadamente.

## Hito 12 — Integración y auditoría técnica

- **Objetivo:** comprobar sistema completo y decidir preparación experimental.
- **Dependencias:** H11 y todos hitos funcionales; ninguna decisión crítica abierta para la versión a congelar.
- **Archivos/módulos:** suite completa, reportes de pruebas/auditoría, runbooks de recuperación y demo.
- **Requisitos:** TR-01–25, 17+28+26 pruebas fuente y pruebas técnicas complementarias.
- **Actividades:** integrar pruebas escritas en cada hito; ejercicio desde carga hasta decisión y BI; revisar seguridad/locks/colas/backup; piloto técnico separado; benchmark 10/30/100 zonas, semillas estrés 501–503, ≥10 repeticiones por tamaño; medir p50/p95/RSS y estados sin aumentar N confirmatorio.
- **Pruebas:** ejecutar 71 criterios fuente (varios parametrizados), GIS/RBAC/BD/concurrencia/BI/recuperación; comprobaciones F7-03/20/24 sobre datos de prueba, repetidas sobre cohorte real H13/H14.
- **Entregables:** reporte con resultados y comandos reales, limitaciones, hardware, perfiles/presupuesto propuestos para congelar.
- **Riesgos:** tratar pruebas simuladas del solver como prueba real, benchmark sin ambiente controlado, excluir fallos.
- **Definition of Done:** sin fallas críticas, regresiones F4/F5 y contratos F7 satisfechos en ámbito de prueba, perfiles/presupuesto aprobados antes de confirmar H13.
- **Aceptación:** checklist técnico respaldado por logs y BD; cualquier prueba no ejecutada queda pendiente y bloquea su criterio, nunca se marca aprobada por revisión.

## Hito 13 — Congelamiento y experimentos confirmatorios

- **Objetivo:** ejecutar exclusivamente protocolo aprobado con muestra fija.
- **Dependencias:** autorización específica H13, H12 aceptado, D03 resuelto por enmienda aprobada, generador/perfiles/solver/semillas/contratos congelados.
- **Archivos/módulos:** fixtures confirmatory, manifests, campaña results, tablas experiments; sólo herramientas implementadas y aprobadas.
- **Requisitos:** TR-21–25; F7 §§3/7/9–11.
- **Actividades:** antes de inspeccionar resultados generar y verificar exactamente E01–E04 × semillas 101–112; 48 fixtures, hashes y 48 prioridades comunes; congelar código/locks/params/red; segunda puerta interna de aprobación del manifiesto antes de ejecutar 96 corridas. Copias lógicas idénticas por método, sin reservas; guardar todas fallas/NA/incumbentes y costos; sin ajustes después de conocer resultados.
- **Pruebas:** identidad de hashes/perfiles por par, 48 IDs/96 intenciones, validador para cada plan válido, oracle inaccesible; auditoría de registros/estados y conteos por familia.
- **Entregables:** 48 pares previstos, 96 registros de ejecución/intención con resultado/fallo/no ejecutado explicado, manifiesto firmado por aprobación humana y evidencia de congelamiento.
- **Riesgos:** timeout, hardware insuficiente, contaminación, edición de fixture a posteriori.
- **Definition of Done:** toda intención tiene estado y evidencia; no hay omisión selectiva. Si no se completan 96 ejecuciones, declarar incompleto y solicitar decisión de reanudación; no declarar cumplimiento total por tener sólo registros de intención.
- **Aceptación:** 96 ejecuciones realizadas o limitación explícita sin falsa aprobación; cero violaciones en planes publicados válidos; pares comparables con mismo input, todos los 48 IDs reportados aunque fallen.

## Hito 14 — Exportación, validación y entrega

- **Objetivo:** entregar resultados auditables y demostración reproducible.
- **Dependencias:** H13 y autorización H14; no rellenar resultados faltantes.
- **Archivos/módulos:** CSV largo/pares, manifest JSON, hashes, reporte factual, capturas Metabase, guía demo/backup.
- **Requisitos:** TR-17–25; F7 §§9/10/12/13.
- **Actividades:** exportar catálogos aprobados, comprobar round-trip BD/CSV/JSON, cuadro de los 48 IDs, tasas de fallos/NA y N efectivo por métrica; estadísticas pareadas por familia/global, bootstrap sólo si fue preregistrado; evidencias BI, restauración y revisión de trazabilidad.
- **Pruebas:** F7-04/20/22/24/25/26 sobre resultados reales; checksum, unicidad, unidades, conteos, reconstrucción de fixture y consulta BI; demo desde copia limpia.
- **Entregables:** paquete reproducible y reporte de ejecución factual con limitaciones; interpretación académica posterior según F7, sin afirmar vidas salvadas ni superioridad institucional.
- **Riesgos:** confundir puntos porcentuales con porcentaje relativo, borrar fallos, km sin contexto de H, sumar litros y kits.
- **Definition of Done:** artefactos consistentes entre sí, pruebas reportadas, resultados negativos preservados, documentación suficiente para reproducir con versiones fijadas.
- **Aceptación:** otro integrante reconstruye entorno, carga resultados y concilia KPI; el informe diferencia calidad técnica, éxito comparativo observado y límites reales.

## Plan experimental invariable y decisiones antes de congelar

| Familia | Zonas / vehículos / unidades / depósitos | Oferta/demanda por tipo | Bloqueos | Faltantes C1–C7 |
|---|---|---|---|---|
| E01 moderada | 8 / 6 / 3 / 2 | 0.90–1.10 | 0–0.05 | 0–0.05 |
| E02 escasez | 12 / 5 / 2 / 2 | 0.40–0.60 | 0–0.10 | 0–0.10 |
| E03 red dañada | 10 / 6 / 3 / 2 | 0.70–0.90 | 0.25–0.40 | 0–0.10 |
| E04 información incompleta | 10 / 6 / 3 / 2 | 0.60–0.80 visible | 0–0.10 | 0.25–0.40 |

Recursos mínimos KIT, AGUA_L y RESCATE; horizonte 6 h y retorno incluido según config F7; primeras 72 h de desastre ficticio. Los rangos no fijan distribuciones ni garantizan cobertura. No descartar una instancia aislada o desfavorable. `as_of` proviene del manifiesto, no del reloj de ejecución.

Doce semillas confirmatorias 101…112 por familia, 48 instancias, 96 ejecuciones pareadas. Piloto propuesto de cuatro instancias E01-1/E02-2/E03-3/E04-4 sujeto a D21. Estrés separado 501…503. Cada par comparte prioridades, demanda observada, flota, stock, red, rutas, horizonte, unidades y ω. FIFO no usa prioridad para decidir. E04 oracle se almacena/monta aparte; sólo evaluación retrospectiva autorizada.

Primarios: H_norm y critical_need_coverage. Secundarios: H_raw, cobertura media, déficits por recurso/tipo, km/horas, km/H, utilización, zonas críticas sin asignación, desconocidos/verificación/intervalos, tiempos/memoria y privación sintética fuera de H. Denominador cero → NA, no cero. Registrar el N válido de cada métrica y cada exclusión, además de los 48 IDs originales.

Análisis: diferencias SIPRE−FIFO por instancia, media/mediana/desviación/extremos/p25/p75 por familia y global, proporciones mejora/empate/empeora; bootstrap opcional preregistrado B=5000, seed=90210, remuestreo por par dentro de familia. No usar zonas o viajes como réplicas independientes. Δkm no demuestra eficiencia cuando H difiere. El éxito de F7 (media ΔH_norm>0 y ΔCrit≥0 donde definido) se mide, no se garantiza; un resultado contrario también se conserva.

Tras congelar, un defecto exige detener y documentar: preservar campaña original, evaluar versión nueva y solicitar aprobación antes de reejecutar, sin reemplazar selectivamente pares. No ajustar objetivos, baseline, métricas ni semillas mirando resultados.

## Seguimiento universitario

Un integrante puede cubrir varios roles propuestos: responsable de proyecto/aprobaciones, backend/BD/seguridad, matemática/GIS, experimentación/QA/BI. No se asignan personas ficticias ni se crean agentes adicionales. Estimar esfuerzo y calendario con disponibilidad real al aprobar H1; priorizar entregas verificables, no prometer plazos sin conocer equipo/hardware. El camino crítico pasa por SRS → datos → seguridad/GIS → motores → decisiones → validación → congelamiento.
