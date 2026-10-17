# Entrega Fase 7 — SIPRE

**Diseño experimental completo; no se han ejecutado experimentos confirmatorios ni programado el simulador.**

## Archivos nuevos

- `SIPRE_EXPERIMENTOS_v1.md`: protocolo, FIFO factible, 4 familias x 12 semillas, KPI, pruebas, análisis y límites.
- `SIPRE_ESCENARIOS_CONFIG_v1.json`: manifiesto parametrizado para generar fixtures; **no son escenarios ya materializados**.
- `SIPRE_RESULTADOS_SCHEMA_v1.json`: contratos de exportaciones y métricas (sin datos reales).
- `PROMPT_CODEX_SIPRE_FASE7.md`: prompt específico para el agente Codex.

## Handoff

1. Entregar junto con Fases 4, 5 y 6 del mismo paquete.
2. La formulación y SRS de Fases 2–3 deben exportarse al repositorio por separado (todavía no existen como archivos locales verificados).
3. Ejecutar Codex primero en modo **planificación**, no implementación.
4. Aprobar/afinar distribuciones del generador y presupuesto solver ANTES de materializar la cohorte principal.
5. Registrar hashes del protocolo y fixtures al congelarse.
6. Sólo después completar F8–F16 y comparar mediante Metabase.

Metabase es exclusivamente lector de vistas `analytics`; un portal operacional registra decisiones humanas.
