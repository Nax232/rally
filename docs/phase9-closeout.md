# Fase 9 — Dictamen de cierre controlado

Fecha: 2026-10-16. Estado: **READY_FOR_REVIEW**. No `CLOSED_AFTER_APPROVAL`: ese estado exige
aprobación humana explícita, que aún no se ha registrado.

## Dictamen y alcance correcto

F9 = H1–H4 del plan F8, según F6 §14. No se inventó un DoD nuevo ni se redujo retroactivamente.
Fase 9 no equivale al Hito 9 de interfaz. Todos los componentes de alcance están implementados y
verificados contra PostgreSQL/PostGIS real.

## DoD y evidencia

| Puerta | Estado | Evidencia |
|---|---|---|
| H1 arranque reproducible/persistencia | Cumplida | Build/arranque en WSL/Docker, migración online, reinicio con servicios `healthy`, backup/restore sin pérdida, alembic head `0004_snapshot_lock` |
| H2 datos/migraciones/integridad | Cumplida | Entidades completas con dominios, FKs, checks (UNKNOWN con NULL, NaN/Inf, geometría 4326, inmutabilidad); migración desde BD vacía y upgrade `0003`→`0004`; pruebas SQL directas de negativos y CRS |
| H3 API/contratos/worker | Cumplida | CRUD con idempotencia y huella de solicitud, snapshots con fingerprint, cola SQL durable con lease/reclamación, worker con verificación de hash y `MAX_ATTEMPTS`, 501 explícito en motores no implementados, seed demostrativo |
| H4 autenticación/roles/auditoría | Cumplida | Sesiones con Argon2id y CSRF, capacidades sin herencia, 401/403/409/422/429/501 verificados, auditoría persistente e inmutable, revocación, límite de intentos |
| Segregación SQL/BI | Cumplida | Lector BI SELECT sobre vista analytics y denegado en dominio/escritura; `sipre_app` denegado en borrar auditoría o alterar saldos; `sipre_worker` denegado en crear usuarios |
| Reconciliación SRS | Documentada | 103 requisitos y ocho objetivos mapeados; C01/C02/C03 requieren decisión del equipo |

Pruebas: **37 aprobadas, 0 omitidas** con BD real; **19 checks E2E** HTTP sin dobles; **16
verificaciones Docker** con 0 fallos. Ruff y Compose config pasan. La suite en contenedor también
da 37. Consulte [evidencia](phase9-test-evidence.md).

## Correcciones aplicadas en esta entrega

- Un único envoltorio de error `{"error":{"code":...,"correlation_id":...}}` para 401/403/404/409/
  422/429/501/503, sustituyendo el `{"detail":...}` por defecto de FastAPI.
- `GET /api/v1/users` (sólo ADMIN, sin `password_hash`) para completar la gestión RBAC.
- Higiene de sesiones: se eliminan sesiones expiradas del usuario en el siguiente login.
- Tests añadidos: conflicto `REVISION_CONFLICT` por revisión obsoleta, aislamiento de snapshot por
  emergencia, inmutabilidad SQL de `model.input_snapshots`, `SNAPSHOT_HASH_MISMATCH` y
  `MAX_ATTEMPTS` del worker, contrato de error 401/403/422, y login sin material de contraseña.

## Qué debe aprobar el equipo

- La interpretación F9 = H1–H4, manteniendo la separación de hitos y sus puertas.
- Ratificación de F2/F3 y resolución registrada de C01 (modo SIMULATED vs real), C02 (cuatro
  estados de emergencia) y C03 (DECISION_MAKER como alias técnico sin herencia). Son propuestas en
  el código, no decisiones ya ratificadas.
- El registro del primer commit de referencia (G09): no se realizan commits automáticos.
- Con la evidencia presente, aceptar el cierre. Sólo una aprobación humana explícita permitirá
  registrar `CLOSED_AFTER_APPROVAL`.

## Pendientes futuros que no bloquean por sí mismos F9

H7 GIS/rutas; H5 AHP-TOPSIS; H6 OR-Tools SIPRE; H8 recomendaciones/decisiones/reservas atómicas;
H9 interfaz; H10 vistas y dashboards Metabase; H11 escenarios/FIFO_FEASIBLE; H12 auditoría
integrada; H13 confirmatorio; H14 exportación.

No se exige implementar motores para cerrar F9. Sí se exigía la integridad de los datos base que
consumirán, y está entregada. Recomendación y decisión siguen como entidades diferentes; generar
recomendaciones no reservará ni despachará automáticamente. Metabase es lector sobre vistas
analytics, con metadatos en base separada.

Protocolo posterior intacto: cuatro familias × doce semillas = 48 instancias y 96 ejecuciones
pareadas con entradas/restricciones equivalentes. D03 sobre selección del presupuesto experimental
sigue pendiente antes del confirmatorio. No se ajustaron fórmulas, escenarios, algoritmos ni
métricas.

## Documentos de esta revisión

- [Trazabilidad](phase9-srs-traceability.md): 103 requisitos F3 y ocho objetivos F2, con evidencia.
- [Brechas](phase9-gap-analysis.md): prioridades, archivos, riesgos, propuestas y decisiones.
- [Pruebas](phase9-test-evidence.md): comandos, resultados y verificaciones ejecutadas.
- Este dictamen: `READY_FOR_REVIEW`, decisión humana pendiente para cerrar.

Próximo paso recomendado: el equipo ratifica alcance/decisiones y acepta o rechaza el cierre. No
avanzar automáticamente entre hitos. El prototipo no se certifica para uso real.
