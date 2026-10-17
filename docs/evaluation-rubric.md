# SIPRE — Pauta de evaluación y evidencia requerida

Fuente: tabla aportada directamente por el usuario al autorizar continuar Fase 9, 2026-10-16. Contiene **cuatro categorías, quince ítems y 90 puntos**. Los ceros de los subtotales en la pauta son campos de evaluación; no son una calificación adjudicada a SIPRE. No se reparten puntos entre ítems porque el usuario no proporcionó ponderaciones individuales.

## Pauta recibida

| Categoría / ítem | Puntaje máximo de categoría |
|---|---:|
| **a) Grado de innovación de la solución propuesta** | **30** |
| La solución es innovadora | |
| El equipo mostró capacidad creativa | |
| El equipo utiliza tecnologías apropiada para el desafío | |
| Grado de usabilidad de la solucion propuesta | |
| **b) Impacto positivo de la propuesta en la sociedad** | **20** |
| La propuesta da solución a una problemática específica | |
| La propuesta idea tiene un valor social por encima de su valor de mercado | |
| La propuesta mejora la calidad de vida de los ciudadanos | |
| **c) Prefactibilidad económica y social y sustentabilidad ambiental** | **20** |
| La propuesta es sustentable desde el punto de vista económico | |
| La propuesta contempla la eficiencia energética y apela a fuentes renovables | |
| La propuesta optimiza el uso de recursos | |
| La propuesta presenta alternativas de mejora a una problematica ambiental específica | |
| **d) Viabilidad técnica de la propuesta** | **20** |
| Base teórica sólida y documentada | |
| El concepto utiliza recursos que son de fácil obtención | |
| La propuesta es acorde a las necesidades de los potenciales usuarios | |
| La solución es técnicamente validada | |

No se asume un criterio adicional de 10 puntos ni se normaliza el total a 100. D23 queda resuelta respecto a la disponibilidad de la pauta; su suma se conserva tal como fue recibida.

## Trazabilidad por ítem (identificadores locales, no del SRS)

| ID | Ítem | Evidencia planificada / relación | Estado al cerrar F9 |
|---|---|---|---|
| PA-A1 | Solución innovadora | F4/F5: combinación explicable AHP-TOPSIS/uncertidumbre/MIP y comparación FIFO; TR-06–12/21–24 | Diseño disponible; demostración comparativa pendiente (H5–H6) |
| PA-A2 | Capacidad creativa | Registro de decisiones, alternativas, iteraciones justificadas y límites; TR-01 | Plan F8 y registro de avance F9 disponibles; no atribuir a equipo trabajo no realizado |
| PA-A3 | Tecnologías apropiadas | Dependencias justificadas, stack abierto, arquitectura modular, prueba de compatibilidad; TR-19 | Python/SCIP comprobados; despliegue completo validado en WSL/Docker (16/16) |
| PA-A4 | Usabilidad | Recorrido por tareas/roles, errores/flags visibles, teclado, observación de usuarios; TR-16, H9 | Portal pendiente; no medir usabilidad con OpenAPI |
| PA-B1 | Problemática específica | Formulación/SRS, caso territorial y restricciones; TR-02–05/11/12 | F2/F3 recibidos y auditados; ratificación pendiente |
| PA-B2 | Valor social | Justificación de necesidades, prioridad humanitaria antes de km, revisión humana y límites; TR-08/11/14 | Diseño disponible; validación con usuarios pendiente |
| PA-B3 | Calidad de vida | Cobertura/déficit/zonas desconocidas como indicadores indirectos en simulación; TR-23 | No existe medición real ni evidencia causal de mejora |
| PA-C1 | Sustentabilidad económica | Inventario hardware/licencias/administración/horas/energía y escenarios de costo; TR-19/25 | Stack sin servicio comercial contratado; costos totales no medidos |
| PA-C2 | Eficiencia energética y fuentes renovables | Medir consumo de ejecución y documentar alternativas de suministro renovable con supuestos/fuentes verificables | **Brecha explícita:** no hay suministro renovable ni medición energética implementados; no equiparar km con energía |
| PA-C3 | Optimización de recursos | Stock/capacidad/activos y déficit, H y utilización vs FIFO; TR-04/05/10/23 | Invariantes de stock/capacidad implementados y probados; motores y experimento pendientes (H5–H6) |
| PA-C4 | Mejora ambiental específica | Definir problemática (p. ej., viajes/consumo en distribución), comparar km y evaluar factores ambientales documentados | Hipótesis a fundamentar, no mejora demostrada; puede aumentar km por prioridad humana |
| PA-D1 | Base teórica | F4/F5, fórmulas, supuestos, fuentes y contraste documental; TR-06/07/10 | Especificaciones disponibles; PDF citado y validación experta ausentes |
| PA-D2 | Recursos de fácil obtención | Instalación local reproducible, software accesible y requisitos de hardware medidos; TR-19 | Locks/README disponibles; runtime Docker habilitado y validado en WSL |
| PA-D3 | Necesidades de usuarios | SRS, capacidades y revisión con roles representativos; TR-02/14/16 | SRS recibido y auditado; evaluación con usuarios pendiente |
| PA-D4 | Validación técnica | Tests ejecutados, logs, constraints, snapshots, concurrencia y BI; TR-01–25 | **37 pruebas** con BD real, **19 checks E2E** y **16 verificaciones Docker**, todas correctas; validación de motores pendiente (H5–H6) |

## Evidencia que no puede sustituirse por afirmaciones

Software gratuito no demuestra sustentabilidad económica total. Menos kilómetros no demuestra ahorro energético sin igual servicio y factores documentados. Datos sintéticos no prueban mejora de calidad de vida real. Una arquitectura documentada no prueba usabilidad ni validación técnica de todo SIPRE.

La pauta orienta evidencia y presentación, no autoriza cambiar H, AHP/TOPSIS, FIFO, semillas, métricas o cohortes para conseguir puntaje. Los escenarios siguen siendo cuatro familias × doce semillas, 48 instancias y 96 ejecuciones pareadas futuras.
