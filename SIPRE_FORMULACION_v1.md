# SIPRE — Fase 2: Formulación académica del proyecto

**Identificador:** SIPRE-F2  
**Versión documental:** 1.0 (consolidación de la Fase 2 desarrollada en esta conversación)  
**Estado:** base académica de diseño; pendiente de ratificación formal por el equipo y de validación con usuarios institucionales.  
**Fecha de consolidación:** 2026-10-16  
**Proyecto:** Sistema de Priorización y Optimización de Recursos en Post-Emergencia (SIPRE).  
**Destinatarios:** equipo del proyecto, Codex (implementación), evaluadores académicos.  
**Fuentes internas:** formulación de Fase 2 realizada en el chat, SRS Fase 3; investigación de Gemini «Investigación para Proyecto SIPRE» (PDF aportado por el usuario). Las afirmaciones normativas, estadísticas y de literatura quedan sujetas a auditoría bibliográfica posterior.

> **Naturaleza del documento:** este archivo materializa la formulación de Fase 2 anteriormente escrita en la conversación. NO constituye aprobación oficial de SENAPRED, COGRID ni otros organismos, ni validación empírica de resultados. Las Fases 4–7 detallan y, cuando corresponde, acotan decisiones técnicas aquí expresadas.

## 1. Título y resumen

**Título:** SIPRE — Sistema de Priorización y Optimización de Recursos en Post-Emergencia.

**Subtítulo:** Sistema de apoyo a las decisiones espaciales para la priorización territorial y la asignación eficiente, explicable y auditable de recursos limitados durante la respuesta inicial a desastres.

**Resumen.** SIPRE es un prototipo académico de *Sistema de Apoyo a las Decisiones Espaciales* (SDSS) diseñado para asistir a coordinadores y autoridades en Chile ante emergencias caracterizadas por necesidades simultáneas, capacidad insuficiente, rutas dañadas y datos incompletos. A partir de información territorial y operacional, el sistema caracteriza ocho dimensiones de criticidad y calcula prioridades relativas mediante ponderación AHP y TOPSIS. Después recomienda la distribución de bienes y equipos mediante optimización matemática bajo restricciones de stock, capacidad, compatibilidad, accesibilidad y disponibilidad. Mantiene una separación obligatoria entre **recomendación del sistema** y **decisión humana**. Sus resultados e indicadores se almacenan en PostgreSQL/PostGIS y se visualizan mediante Metabase. La utilidad del prototipo se evaluará con escenarios **sintéticos y reproducibles**, comparando una estrategia FIFO factible con SIPRE utilizando las mismas entradas y restricciones. La evaluación no acreditará por sí sola aptitud para operación real.

## 2. Contexto y problemática

Después de un terremoto, inundación, aluvión, tsunami, incendio de gran escala u otro desastre pueden coexistir interrupciones de comunicaciones, rutas bloqueadas, infraestructura crítica dañada, comunidades aisladas, servicios básicos interrumpidos y demandas urgentes muy superiores a la capacidad inicial de respuesta. Las autoridades deben actuar antes de contar con un diagnóstico consolidado de daños.

En el contexto chileno existen instrumentos de registro y coordinación institucional, entre ellos reportes preliminares y catastros posteriores como ALFA y FIBE. SIPRE **no reemplaza** esos instrumentos ni pretende acceder automáticamente a sus sistemas internos; busca apoyar la toma de decisiones durante la ventana en la que los datos son fragmentarios o de calidad desigual. Las referencias a atribuciones concretas de las instituciones deben verificarse contra fuentes oficiales antes de su publicación final.

**Problema formal:** durante la fase inicial posterior a una catástrofe, los equipos encargados de coordinar la respuesta deben decidir qué territorios atender y cómo distribuir recursos humanos, materiales y logísticos escasos entre necesidades simultáneas, con información incompleta, desactualizada, contradictoria y restricciones cambiantes de accesibilidad.

**Oportunidad:** convertir información territorial y operacional verificable —y representar su incertidumbre— en recomendaciones cuantificadas que faciliten comparar alternativas de asignación, documentar restricciones y sustentar decisiones humanas.

## 3. Pregunta e hipótesis de investigación

**Pregunta principal:** ¿Cómo puede un sistema de apoyo a decisiones espaciales integrar información territorial incompleta, priorización multicriterio y optimización matemática para recomendar una distribución humanitariamente priorizada, logísticamente factible, explicable y auditable de recursos limitados durante las primeras etapas de una post-emergencia?

**Preguntas secundarias:**
1. ¿Qué dimensiones territoriales y sociales permiten caracterizar la criticidad de una zona?
2. ¿Cómo representar reportes insuficientes, contradictorios o desactualizados sin convertir desconocimiento en ausencia de necesidad?
3. ¿Cómo distribuir existencias y unidades indivisibles bajo restricciones operacionales y viales?
4. ¿Cómo hacer transparente la justificación de una recomendación y conservar la intervención humana?
5. ¿Qué diferencias medibles se observan frente a una estrategia simple y factible bajo los mismos escenarios simulados?

**H1 (a contrastar):** al combinar priorización territorial multicriterio y optimización logística, SIPRE podrá obtener en ciertos escenarios simulados de recursos escasos una cobertura humanitaria ponderada superior a la de una asignación FIFO factible, sujeto a restricciones iguales y sin asumir mejores resultados en todas las métricas.

**H0:** en los escenarios ensayados no se identifica una mejora relevante de SIPRE frente a FIFO en los indicadores primarios preregistrados.

Ninguna hipótesis es un resultado ni una promesa operacional. La metodología y los criterios de éxito se detallan en `SIPRE_EXPERIMENTOS_v1.md`.

## 4. Objetivos

### Objetivo general
Diseñar, implementar y validar a nivel de prototipo académico un sistema de apoyo a decisiones espaciales capaz de priorizar zonas afectadas y recomendar la asignación de recursos limitados en post-emergencia, mediante información geoespacial, evaluación multicriterio, optimización matemática, representación explícita de incertidumbre y supervisión humana.

### Objetivos específicos
- **OE-01 — Integración territorial:** estructurar información territorial, poblacional y operacional con procedencia, unidades, fecha y calidad.
- **OE-02 — Caracterización:** representar gravedad humana, población afectada, vulnerabilidad, infraestructura crítica, accesibilidad, servicios básicos, tiempo sin asistencia e incertidumbre.
- **OE-03 — Priorización:** establecer ponderaciones mediante AHP y calcular prioridades territoriales mediante TOPSIS, según su especificación técnica versionada.
- **OE-04 — Manejo de información incompleta:** distinguir datos observados, estimados y desconocidos, y señalar necesidades de verificación sin imputarlas como hechos.
- **OE-05 — Asignación:** construir un modelo matemático que proponga distribuciones factibles de bienes transportables y unidades especializadas, sujetas a recursos y rutas disponibles.
- **OE-06 — Apoyo a la decisión:** producir recomendaciones con explicaciones, déficits visibles, restricciones y un ciclo explícito de revisión/aprobación humana auditada.
- **OE-07 — Visualización:** disponer resultados e indicadores analíticos en Metabase sin otorgarle capacidades de aprobación transaccional.
- **OE-08 — Validación:** comparar el modelo SIPRE con FIFO_FEASIBLE en escenarios sintéticos reproducibles, evaluando cobertura, faltantes, logística, factibilidad, reproducibilidad e incertidumbre.

## 5. Alcance y límites

**Ámbito temporal orientativo:** primeras 24–72 horas de una emergencia; el horizonte concreto de cada corrida de asignación es configurable, no equivale automáticamente a 72 h.

**Ámbito territorial:** zonas o sectores de una emergencia simulada, representados mediante identificadores y geometrías o localizaciones coherentes; los resultados de priorización corresponden a un escenario y corte temporal concretos.

**MVP incluido:**
- Creación y estado de emergencias/escenarios, zonas y reportes territoriales.
- Datos basales, fuentes y calidad; necesidades observadas o estimadas aprobadas y necesidades desconocidas.
- Bodegas, inventarios, vehículos, unidades especializadas y recursos compatibles.
- Red vial de escenario, accesos confirmados en el escenario y bloqueos.
- Cálculo AHP/TOPSIS, evolución temporal y señales de incertidumbre.
- Optimización lexicográfica de recursos y rutas para **una salida/un destino por vehículo** dentro del ciclo MVP, según Fase 5.
- Recomendaciones y déficits explícitos; evaluación, modificación de supuestos/restricciones y aprobación humana separada.
- Historial, snapshots y trazabilidad de corridas; dashboards de Metabase OSS.
- Simulación y comparación contra FIFO_FEASIBLE.

**Exclusiones del MVP:** alerta temprana, triaje clínico individual, predicción exacta de víctimas, integración directa en vivo con ALFA/FIBE/SENAPRED, despacho automático, GPS de flota en tiempo real, comunicaciones nacionales garantizadas, drones, IoT, aplicación ciudadana, CVRP multiparada completo, certificar transitabilidad vial real y funcionamiento sin servidor ni energía.

**Limitación de seguridad:** la confirmación humana en SIPRE registra una decisión simulada o documentada; no significa que se haya realizado un despacho real ni que exista certificación para utilizar el sistema en emergencias reales.

## 6. Usuarios, beneficiarios y stakeholders

**Actores lógicos del software:**
- **Administrador:** cuentas, parámetros tecnológicos y configuración autorizada.
- **Operador:** reportes, zonas, necesidades, inventario y restricciones.
- **Analista:** prepara escenarios y ejecuta modelos de priorización/optimización.
- **Autoridad o decisor:** revisa, rechaza, modifica restricciones y confirma/rechaza planes según autorización.
- **Observador:** consulta datos y resultados permitidos sin editar información operacional.

**Stakeholders y potenciales usuarios institucionales:** equipos comunales y regionales de gestión de emergencias, coordinadores logísticos, áreas técnicas de municipalidades, personal de respuesta y organismos competentes en el marco chileno, sujetos a validación de sus atribuciones y necesidades reales. **No se afirma que SENAPRED ni ningún organismo haya solicitado, probado o aprobado SIPRE.**

**Beneficiarios potenciales:** comunidades afectadas, incluidas personas y territorios vulnerables o aislados. Los beneficios son **hipótesis de impacto**, no resultados comprobados.

## 7. Propuesta de solución y proceso

1. Registrar/importar emergencia y zonas con datos basales y evidencia georreferenciada.
2. Incorporar reportes con unidad, fuente, hora de observación, hora de registro y calidad.
3. Validar coherencia, conservar desconocidos, preparar snapshot de entradas.
4. Obtener pesos AHP versionados y calcular prioridades mediante TOPSIS con referencias ancladas según F4.
5. Guardar puntuaciones, factores, incertidumbre, límites de sensibilidad y marcas de verificación.
6. Combinar prioridades con demandas conocidas/aprobadas, stock libre, capacidad, compatibilidad, activos y rutas verificadas para un horizonte específico.
7. Optimizar lexicográficamente: **primero** cobertura humanitaria ponderada H; **después** costo logístico sujeto a preservar el resultado humanitario dentro de tolerancia aprobada.
8. Emitir recomendaciones y faltantes con explicación; no reservar/despachar por mera recomendación.
9. Permitir aprobación/rechazo/modificación humana, con nueva comprobación de vigencia de stock, bloqueos y perfiles antes de confirmar.
10. Exponer resultados agregados a Metabase a través de vistas de sólo lectura y registrar auditoría.

**Principio rector:** SIPRE recomienda; la autoridad humana decide.

## 8. Principios científicos, éticos y operacionales

- **Primacía humanitaria:** el objetivo primario es cobertura priorizada de necesidades conocidas; los kilómetros no se compensan libremente contra esa cobertura.
- **Equidad territorial:** la lejanía o escasez de reportes no deben interpretarse automáticamente como ausencia de necesidad.
- **Incertidumbre explícita:** NULL no equivale a cero. El índice de incertidumbre no prueba daño ni genera un despacho autónomo.
- **Explicabilidad:** informar ponderaciones, principales factores, restricciones, déficit y calidad de datos; no afirmar que una suma lineal sea la contribución exacta al puntaje TOPSIS.
- **Intervención humana:** una recomendación y una decisión son entidades diferenciadas; confirmaciones con justificación y trazabilidad.
- **No discriminación indirecta:** vigilar posibles sesgos por disponibilidad desigual de datos, ruralidad, accesibilidad y cobertura digital.
- **Privacidad:** preferir indicadores agregados y mínimo dato personal; evitar publicar información de salud sensible en dashboards abiertos.
- **Honestidad experimental:** no presentar simulaciones como uso institucional real ni atribuir mejoras de la literatura al prototipo.

## 9. Innovación y contribución esperada

**Innovación planteada (no declarada mundialmente única):** integrar, para un caso académico de post-emergencia en Chile, análisis multicriterio territorial, temporalidad de necesidades, incertidumbre, rutas de escenario, optimización lexicográfica humanitaria, explicación de decisiones y supervisión humana dentro de un flujo reproducible.

El diferencial no radica en inventar AHP, TOPSIS, OR-Tools o Metabase, sino en su integración con las restricciones y necesidades específicas identificadas en el desafío.

## 10. Impacto social esperado (no demostrado aún)

**Resultados potenciales sujetos a validación:** mejor cobertura de necesidades prioritarias; transparencia sobre zonas no atendidas; mejor documentación de decisiones; menor posibilidad de que una zona silenciosa sea tratada como segura; utilización más informada de capacidades limitadas.

**Indicadores relacionados:** cobertura humanitaria ponderada, cobertura de demandas conocidas en zonas críticas, demanda no cubierta por clase, cantidad de zonas prioritarias sin asignación, utilización de activos, distancia logística y tiempo computacional. No interpretar las puntuaciones como vidas salvadas o mortalidad evitada.

## 11. Prefactibilidad económica, social y sustentabilidad ambiental

- **Técnica/económica preliminar:** stack previsto mayoritariamente libre/abierto para prototipo (Python, FastAPI, PostgreSQL/PostGIS, OR-Tools, Metabase OSS, Docker Compose). Los costos de desarrollo, operación, equipo, capacitación, hosting, energía, seguridad y mantenimiento existen y deberán presupuestarse: «costo cero» no es una afirmación válida.
- **Social:** adopción requiere capacitación, validación con potenciales usuarios y procesos existentes de coordinación; se desconoce actualmente el grado de aceptación de actores reales.
- **Ambiental:** minimizar recorridos/carga redundante podría disminuir combustible, pero sólo se afirmará una mejora si la experimentación demuestra una reducción bajo iguales necesidades humanitarias. No afirmar que utilice renovables, ni inventar una instalación fotovoltaica.
- **Sustentabilidad funcional:** versiones de datos/modelos, trazabilidad, documentación, pruebas y posibilidad de operación local con fuentes externas caídas cuando sigan disponibles el servidor y la red local.

## 12. Viabilidad técnica propuesta

Arquitectura definida de forma más precisa en F6: backend Python/FastAPI en monolito modular; base PostgreSQL/PostGIS; motor AHP/TOPSIS independiente y motor OR-Tools lexicográfico separado; grafo vial sintético versionado para el MVP; UI operacional mínima de transacciones; Metabase OSS de **sólo lectura** sobre vistas `analytics`; Docker Compose y pruebas automáticas. No se presupone conectividad con bases protegidas de organismos públicos.

La **viabilidad definitiva no se declara validada**: requiere implementar prototipo, ejecutar tests de F4/F5, verificar integridad y reproducibilidad del protocolo F7, controlar acceso y documentar limitaciones.

## 13. Riesgos y mitigaciones preliminares

| Riesgo | Mitigación de diseño | Validación prevista |
|---|---|---|
| Datos faltantes/confusos | Estados observado/estimado/desconocido, procedencia, límites de sensibilidad | F4 + tests de ingesta |
| Reportes sesgados geográficamente | Incertidumbre, bandera de verificación y datos basales | E04, análisis de sensibilidad |
| Rutas inexistentes | Sólo arcos habilitados del escenario; rutas versionadas | E03, tests GIS |
| Sobreasignación | Restricciones stock/capacidad y reservas transaccionales | F5 + tests concurrencia |
| Dependencia de algoritmo | Explicaciones y aprobación humana explícita | Tests autorización y UI |
| Falta de adopción | Interfaz simple y pruebas con usuarios, si se logra acceso | Plan de validación de usabilidad |
| Falta de conexión externa | Uso local de datos almacenados, dependencia de energía/servidor reconocida | Tests modo degradado |
| Métricas engañosas | Diseño experimental pareado y preregistrado | F7, auditoría de resultados |
| Exposición de datos | RBAC, vistas agregadas y acceso Metabase limitado | Tests roles/permisos |

## 14. Evaluación académica — criterios de la pauta

La pauta aportada en la conversación considera cuatro bloques principales (90 puntos visibles): innovación (30), impacto positivo (20), prefactibilidad económico-social y sustentabilidad ambiental (20), viabilidad técnica (20). No se presume que estos sean todos los componentes de la evaluación original.

| Bloque | Argumento que plantea la solución | Evidencia futura (no inventar) |
|---|---|---|
| Innovación (30) | Integración priorización + optimización + incertidumbre + HITL | Demo extremo a extremo, explicación, escenarios |
| Impacto positivo (20) | Cobertura humanitaria, déficit, equidad territorial | KPI sobre escenarios y discusión de límites |
| Prefactibilidad y sustentabilidad (20) | Tecnologías accesibles y optimización logística subordinada a cobertura | Costeo razonado, km, uso de recursos |
| Viabilidad técnica (20) | Modelos formales, API, base relacional/espacial, pruebas | Tests ejecutados, Docker, resultados reproducibles |

## 15. Validación experimental planificada

Métodos: **FIFO_FEASIBLE** como estrategia base y SIPRE como estrategia optimizada, con igual escenario, semilla, demandas, stock, flota y red vial. Se prevén 4 familias sintéticas × 12 semillas = 48 instancias y 96 ejecuciones pareadas, según `SIPRE_EXPERIMENTOS_v1.md`. El baseline también debe ser físicamente factible. No modificar el conjunto confirmatorio a posteriori para favorecer SIPRE.

Se informarán resultados favorables y desfavorables, fallos del solver, tiempo de cómputo, diferencias entre beneficio humanitario y distancia, y validez limitada a supuestos y escenarios simulados.

## 16. Supuestos, restricciones y pendientes

**Supuestos del prototipo:** acceso a un ordenador compatible con Docker, datos sintéticos/controlados, recursos definidos con unidades, escenarios espaciales preconfigurados y decisión humana representada mediante usuario autorizado.

**Restricciones:** no hay validación institucional, financiación operacional ni inventarios nacionales accesibles; las capacidades de Metabase OSS y la compatibilidad de versiones deben verificarse en entorno instalado; rutas marcadas «verificadas» sólo lo son respecto del dataset del escenario.

**Pendientes de ratificación del equipo:** disponibilidad de usuarios para revisión, aprobaciones finales de pesos y umbrales, perfil de hardware, política real de backup, elección final de UI ligera, presupuesto económico y niveles de desempeño aceptables. No atribuir a especialistas pesos sintéticos.

## 17. Documentos derivados y precedencia

- **F3:** `SIPRE_SRS_v1.md` — requisitos y criterios de aceptación.
- **F4:** `SIPRE_PRIORIZACION_v1.md` — ecuaciones AHP/TOPSIS, normalización, datos faltantes.
- **F5:** `SIPRE_OPTIMIZACION_v1.md` — restricciones y objetivo lexicográfico, baseline.
- **F6:** `SIPRE_ARQUITECTURA_v1.md` — módulos, DB/API, seguridad, Metabase, transacciones.
- **F7:** `SIPRE_EXPERIMENTOS_v1.md` — escenarios, pruebas, métricas, integridad y reproducción.

**Regla de precedencia:** el objetivo y alcance están en F2; las necesidades funcionales en F3; los **algoritmos exactos** en F4/F5; la **implementación técnica** en F6; el **protocolo confirmatorio** en F7. Si dos fuentes discrepan, Codex debe registrar la discrepancia y elevarla para aprobación; no elegir silenciosamente.

**Cierre documental:** formulación académica consolidada para uso en prototipo, sujeta a aprobación del equipo y validación institucional futura antes de realizar cualquier uso operacional.
