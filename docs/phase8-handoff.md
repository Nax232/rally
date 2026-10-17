# SIPRE — Handoff ejecutivo de Fase 8

Fecha: 2026-10-16. Estado: **Fase 8 planificada para aprobación; implementación no comenzada**. No se ejecutaron simulaciones confirmatorias, no se generaron escenarios definitivos, no se instalaron dependencias ni se inició Git.

Nota histórica: ese estado describe la entrega F8. Posteriormente el usuario autorizó continuar F9 y aportó la pauta. El progreso actual y los bloqueos están en [phase9-status.md](phase9-status.md); el usuario indicó que aportará F2/F3. No interpretar este handoff histórico como ausencia de autorización para la infraestructura ya iniciada.

## Qué recibió y revisó esta fase

Carpeta `C:\Users\Matias\Downloads\Rally` con trece archivos de especificación/entrega. Se leyeron completos los diez documentos obligatorios disponibles de F4–F7 y tres auxiliares. Faltan `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md`; además no se dispone de pauta íntegra/PDF citado. No hay AGENTS aplicable encontrado, código, pruebas, Compose, locks ni repo Git inicializado. Git instalado 2.55.0.windows.2; Python operativo no reconocido por launcher y Docker no localizado en comprobaciones habituales.

Comprobado en F8: seis JSON parseables; seis checksums del manifiesto F7 coincidentes; valores de ejemplo TOPSIS compatibles con tolerancia en cálculo aritmético en memoria. **No** equivale a ejecutar ni aprobar las 71 pruebas fuente. No hay software funcional que certificar.

## Diseño que debe mantenerse

Monolito modular FastAPI, PostgreSQL/PostGIS con ocho esquemas y base `metabase_app` separada, API/worker con mismo código y cola SQL persistente, motores puros AHP/TOPSIS y MIP lexicográfico OR-Tools/SCIP, GIS NetworkX de escenario, portal Jinja2/HTMX propuesto y Metabase OSS como único BI, sólo lectura.

MVP de un destino/salida/vehículo. F4 produce prioridad, intervalos y explicaciones; no demanda. F5 maximiza H antes de costo, respeta R01–R13 y no vuelve a ponderar tiempo C7. Snapshot/perfiles inmutables. `Recommendation` separada de `Decision`; sólo aceptación humana autorizada reserva stock/activos transaccionalmente. Ningún cálculo, experimento o tarjeta de BI emite una orden operacional.

Configuración demo local propuesta: cuatro procesos/contenedores `db`, `api`, `worker`, `metabase`, más tarea puntual de migraciones. Una instancia Postgres puede alojar dos bases con usuarios distintos. Bind localhost, secretos externos, logs sin PII, backups de ambas bases. Python 3.12, PostgreSQL 16/PostGIS 3.5, OR-Tools 9.15/SCIP, FastAPI/Pydantic v2 y demás líneas candidatas en dependencies; pins/digests y compatibilidad efectiva pendientes H1.

## Lectura de documentos entregados

| Documento | Uso al continuar |
|---|---|
| [implementation-plan.md](implementation-plan.md) | 14 hitos, dependencias, actividades, pruebas, entregables, riesgos, DoD, aceptación y protocolo experimental |
| [repository-structure.md](repository-structure.md) | Árbol objetivo, responsabilidades, límites entre algoritmos/HTTP/SQL/BI |
| [architecture-review.md](architecture-review.md) | Auditoría real, arquitectura comprendida, datos, jobs, concurrencia y dictamen condicionado |
| [dependencies.md](dependencies.md) | Stack candidato, fuentes primarias, compatibilidad a probar y presupuesto local propuesto |
| [testing-strategy.md](testing-strategy.md) | 71 criterios fuente y pruebas técnicas, oráculos/tolerancias, comandos futuros y evidencia |
| [risks-and-decisions.md](risks-and-decisions.md) | D01–D25 abiertas, R01–R12 y responsables/puertas |
| [requirements-traceability.md](requirements-traceability.md) | TR-01–25 provisionales, R01–R13, hitos/pruebas/pauta; no inventa RF/RNF |
| [phase8-handoff.md](phase8-handoff.md) | Este resumen y alcance concreto de la próxima autorización |

## Orden de desarrollo y autorizaciones

H1 infraestructura → H2 datos → H3 API/jobs → H4 seguridad → **H7 GIS** → H5 priorización → H6 optimización → H8 decisión/audit → H9 portal → H10 Metabase → H11 generador/FIFO/KPI → H12 auditoría/piloto → H13 confirmatorio → H14 exportación.

Se adelanta H7 por dependencia de C5 y factibilidad; se mantienen números del pedido. Cada hito requiere autorización expresa antes de comenzar. Aceptar este plan no habilita automáticamente todos los hitos. H13 contiene además puerta interna: validar y aprobar manifiesto congelado antes de ejecutar los 96 runs.

## Decisiones que requieren respuesta del equipo

1. **D01:** aportar formulación y SRS aprobados (y pauta completa D23), o autorizar H1 exclusivamente de infraestructura mientras se aportan. No cerrar trazabilidad formal ni comenzar H2 con requisitos inventados.
2. **D02/D15:** ratificar monolito, portal Jinja2/HTMX, sesiones de servidor, worker con cola PostgreSQL y bases separadas en una instancia local. Son propuestas concretas de diseño, no tecnologías ya implementadas.
3. **D03:** aprobar enmienda a F7 §8.7: no elegir presupuesto con E02-101/E03-101/E04-101 antes de confirmar. Usar piloto para elegirlo; sensibilidad de esas instancias sólo después como exploratoria. No se alteraron los originales.
4. **D04–D11/D17/D18/D21/D22:** ratificar perfiles DEMO completos, distribuciones/topología/RNG, presupuesto por etapa/incumbentes, unidades/IDs/estados, catálogo KPI, empates, selección de rutas y detalles de piloto/controles. Se resuelven antes de sus puertas, no es necesario improvisarlos para iniciar infraestructura.
5. **D12–D14:** aprobar capacidades, responsable de estimaciones, vigencia, modificación/liberación y reservas; son necesarios para seguridad y decisión humana.

Toda aprobación se registra con ID, autor, fecha, versión afectada y pruebas. Ningún silencio autoriza cambios. El motivo de detener la programación es la instrucción explícita del usuario: «Espera mi aprobación antes de programar» y «No avances automáticamente entre hitos sin autorización».

## Paquete concreto para autorizar H1

**Alcance solicitado:** inicializar un nuevo repositorio local en esta carpeta si el equipo confirma que es el destino, conservar íntegros los trece archivos fuente, crear esqueleto de paquete/documentación, manifiestos y locks, configuración Docker Compose/Dockerfile, `.env.example` sin secretos, configuración de pruebas y smoke checks de dependencias. No desarrollar reglas de negocio, modelos matemáticos, generador definitivo ni confirmatorio dentro de H1.

**Prerequisitos:** aprobación del plan y H1 limitado; acceso a runtime de contenedores local y recursos disponibles. Provisionar instalación de sistema sólo bajo autorización que corresponda; no presuponer Docker instalado. Si se aporta un checkout real, volver a auditar Git/AGENTS y adaptar sin sobrescribir trabajo.

**Secuencia H1 ya definida:** verificar Git/AGENTS actualizados → registrar aprobación y hashes → seleccionar/resolver versiones y comprobar licencias → construir imagen Python → levantar BD/Metabase locales → imports/SCIP/health checks → reinicio/persistencia → documentar versiones y comandos → entregar revisión y detenerse antes de H2.

**Criterio de cierre H1:** instalación reproducible en entorno limpio autorizado, dependencias compatibles comprobadas, volúmenes persistentes, secretos fuera de repo, fuentes conservadas y evidencia de comandos/resultados. Si un smoke falla, no declarar H1 aprobado ni continuar.

## Reglas para futuro experimental

Cuatro familias E01–E04, semillas 101–112 por familia, **48 instancias y 96 ejecuciones pareadas**. Datos/perfiles/restricciones idénticos por par, oracle E04 físicamente inaccesible a algoritmos, FIFO por UTC/request_id sin prioridad para asignar; evaluador H/factibilidad común. Piloto/estrés/exploratorio separados. Congelar generador, fixtures, código, presupuesto y métricas antes de resultados. Conservar timeouts/NA/fallos y 48 IDs completos. No ajustar muestra/modelos/métricas para favorecer SIPRE. No producir conclusiones de impacto real a partir de datos sintéticos.

## Registro de preservación de fuentes

Además de las seis entradas comprobadas del manifiesto F7 original, estos hashes permiten verificar las fuentes de modelos/arquitectura y el propio manifiesto sin Git:

| Archivo | SHA-256 al auditar F8 |
|---|---|
| SIPRE_PRIORIZACION_v1.md | fccb9130e6f911347397c207c734849a2c56fb2814c930db268a688e9981fc99 |
| SIPRE_PRIORIZACION_EJEMPLO.json | 1964b801af77c67ee9786b63ee76e01e3a6b7b4e0a00dd732e35b9f1685a84a5 |
| SIPRE_OPTIMIZACION_v1.md | 9e8003d7562c761c5dd5f7d071ef071686010bd36584bdd3228d5411a0c33d67 |
| SIPRE_OPTIMIZACION_EJEMPLO.json | dabdcedddd66eec49f8ab12f2f8ed565ce12cb0d4b635aa9453d978edd2e2880 |
| SIPRE_ARQUITECTURA_v1.md | 5d5d5b81563f083d32163530afbf567e47e82288ac6233a07803e0e493d38c18 |
| SIPRE_CONTRATOS_FASE6_v1.json | 4220be02fbfc61463080c7262e1f5e4f273fdc747750998af275e0f8ba13d0f3 |
| SIPRE_FASE7_SHA256.txt | 68bdf2458dca079436f885eb7fd7e9f56cfa107e88f95ca69b3bd1f5c8041e29 |

Fase 8 entrega ocho documentos reales. Las fuentes no se corrigieron, trasladaron ni borraron; los cambios de modelo/protocolo pendientes sólo se proponen en el registro de decisiones. **La Fase 8 quedó planificada, pero la implementación no ha comenzado.**


## Actualización de auditoría F9 — 2026-10-16

F2 y F3 ya están disponibles como `SIPRE_FORMULACION_v1.md` y `SIPRE_SRS_v1.md` en la raíz y fueron revisados completos. Las referencias anteriores a su ausencia describen el estado previo. D01 queda subsanada en cuanto a recepción; ratificación y discrepancias quedan pendientes. La Fase 9 permanece **BLOCKED** por infraestructura sin validación online y H2–H4 incompletos. La revisión actual sólo modifica documentación. Dictamen vigente: [phase9-closeout.md](phase9-closeout.md).

