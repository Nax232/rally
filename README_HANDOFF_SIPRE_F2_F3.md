# Entrega de la formulación y el SRS de SIPRE a Codex

## Qué incluye este paquete

1. `SIPRE_FORMULACION_v1.md` — contenido consolidado de Fase 2 (objetivos, alcance, hipótesis, impacto, partes interesadas, restricciones y límites).
2. `SIPRE_SRS_v1.md` — contenido consolidado de Fase 3 (65 RF, 15 RNF, 5 RQD, 12 RN, 6 RX, actores, flujos, casos de error y matriz de trazabilidad).
3. `PROMPT_CODEX_CIERRE_FASE9_CON_F2_F3.md` — instrucciones para reconciliar estos documentos con la Fase 9 ya implementada.

## Uso sugerido

- Copia F2 y F3 a `docs/specs/` del repositorio (o a la carpeta de especificaciones que utilice el equipo).
- Añade/commitea los documentos como fuente de requisitos versionada. No los uses para reescribir un prototipo existente sin auditar diferencias.
- Ejecuta el prompt con Codex desde la raíz del repositorio.
- Codex primero debe **auditar y planificar las correcciones**, no realizar un rediseño total.
- Define aprobación humana para cambios en matemáticas, seguridad, modelos y reglas de negocio.

## Advertencia de estado

Los contenidos de F2/F3 fueron desarrollados previamente en la conversación y aquí se **consolidan** para que Codex pueda leerlos. La conversación los marcó como fases de diseño completas, pero no constituye firma formal del equipo, certificación institucional ni validación mediante usuarios reales. El equipo debe revisar y aprobar esta versión documental. No se afirma que la Fase 9 o los tests estén completados hasta comprobar el repositorio.

## Fuentes especializadas

Las Fases 4–7 constituyen referencias de detalle: F4 priorización matemática, F5 optimización logística, F6 arquitectura y contratos, F7 experimentación. Si surge contradicción o un requisito ambiguo, Codex debe documentarlo y solicitar decisión del equipo. **Las funciones de etapas futuras no son criterio obligatorio para cerrar un hito de infraestructura Fase 9** salvo que el roadmap explícitamente lo disponga.
