# Prompt para Codex — Incorporación de Fases 2 y 3 y cierre controlado de Fase 9

Actúa como **Codex, Tech Lead y auditor de implementación del proyecto SIPRE**. Ya existe trabajo técnico realizado para la **Fase 9 (base de infraestructura/backend y datos según el roadmap del repositorio)**. Acabo de aportar los dos documentos cuya ausencia impedía contrastar esa implementación con los objetivos y requisitos de origen:

- `docs/specs/SIPRE_FORMULACION_v1.md` (Fase 2)
- `docs/specs/SIPRE_SRS_v1.md` (Fase 3)

Además, debes conservar y consultar las especificaciones F4–F7 y las decisiones aprobadas en el repositorio. Si esos archivos ya existen en otra ruta, localízalos y utiliza las rutas verdaderas. **No asumas que el ZIP por sí solo significa que los archivos están instalados en el repositorio.**

## Objetivo de este turno

**No reiniciar el desarrollo ni reemplazar la base técnica existente.** Inspecciona la implementación real de Fase 9, revisa su conformidad con F2/F3 y emite un diagnóstico con correcciones acotadas y un veredicto justificable sobre la finalización de Fase 9.

## Tareas

1. Lee `AGENTS.md` si existe; inspecciona Git, estructura, documentación, dependencias y tests disponibles. No realices operaciones destructivas.
2. Lee F2 y F3 completos; el SRS agrupa RF-001–RF-065, RNF-001–RNF-015, RQD-001–RQD-005, RN-001–RN-012 y RX-001–RX-006. Revisa además las restricciones específicas de F4, F5, F6 y F7, pero **no implementes funciones de sus hitos posteriores sólo para declarar cerrada Fase 9**.
3. Determina el alcance real/Definition of Done de Fase 9 conforme al plan técnico del repositorio. Si no existe una definición formal, **repórtalo y proponla**, sin inventar que ya estaba aprobada.
4. Construye matriz requisito de F2/F3 → módulo/hito → estado: `IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_NOT_TESTED`, `MISSING_IN_F9_SCOPE`, `PLANNED_LATER`, `CONFLICT`, `NOT_APPLICABLE`. No marques un requisito `PASS` simplemente porque está documentado o porque el código parece existir.
5. Verifica requisitos críticos aplicables a Fase 9: migraciones válidas, entidades y restricciones BD, fuentes y timestamps, demanda `NULL` distinta de 0, stock/identidad física, campos espaciales con CRS, seguridad mínima aplicable, configuración `.env.example`, Docker Compose, health checks, tests, preservación de datos históricos y segregación de Metabase cuando corresponda.
6. Identifica discrepancias con el SRS; F4/F5 son fuentes de verdad de matemáticas, F6 de arquitectura técnica y F7 de simulación. No reescribas silenciosamente especificaciones para adaptar el código a posteriori. Diferencia **aclaración/refinamiento** de **contradicción real**.
7. Ejecuta las pruebas y validaciones locales disponibles y reporta **comandos, resultados, fallos y causas**. Si no tienes acceso a Docker, base de datos u otras dependencias, declara el bloqueo; no inventes que las pruebas pasaron.
8. En esta primera revisión, **no modifiques código** salvo que reciba aprobación expresa. Entrega primero propuesta priorizada de correcciones. Si ya existe una autorización del usuario para corregir errores en F9, limítate estrictamente a ese alcance y no cambies modelos matemáticos, esquema de experimentos ni seguridad sensible sin aprobación.
9. Cuando se autorice, realiza las correcciones necesarias sobre el repositorio actual, añade tests y vuelve a ejecutar validaciones antes de proponer el cierre.
10. Mantén la separación: recomendación ≠ decisión confirmada, y Metabase de sólo lectura. No pretendas certificar este prototipo para uso real.

## Entregables

- `docs/phase9-srs-traceability.md`: matriz de cumplimiento F2/F3 vs hitos y evidencia real.
- `docs/phase9-gap-analysis.md`: discrepancias por severidad, archivos afectados, propuesta y riesgo.
- `docs/phase9-test-evidence.md`: comandos de prueba y resultados observados.
- `docs/phase9-closeout.md`: estado de cierre de Fase 9 (`READY_FOR_REVIEW`, `BLOCKED`, `CLOSED_AFTER_APPROVAL`); pendientes de fases futuras separados.

## Criterio de cierre

Fase 9 puede proponerse como `READY_FOR_REVIEW` únicamente cuando todos los requisitos **aplicables al hito 9** tengan evidencia verificable suficiente, migraciones/pruebas pertinentes pasen y no existan defectos bloqueantes. **No exijas tener implementados F4–F7** si el plan los dejó para fases posteriores.

Antes de afirmar cierre definitivo, indícame qué aprueba el equipo, qué queda pendiente y qué pruebas pudiste ejecutar realmente. El equipo humano conserva la decisión de declarar una fase cerrada.
