# Fase 9 — Dictamen de cierre controlado

Fecha de revisión y aprobación humana: 2026-10-17. Estado: **CLOSED_AFTER_APPROVAL**.
El usuario aprobó explícitamente cerrar Fase 9 al indicar «demos por finalizada la fase 9 y sigamos con la fase 10».
La aprobación cubre F9 = H1–H4 y conserva el alcance `SIMULATED`; no certifica uso operacional.

## Dictamen y alcance correcto

F9 = H1–H4 del plan F8, según F6 §14. No se inventó un DoD nuevo ni se redujo retroactivamente.
Fase 9 no equivale al Hito 9 de interfaz. Todos los componentes de alcance están implementados y
verificados contra PostgreSQL/PostGIS real.

## DoD y evidencia

| Puerta | Estado | Evidencia |
|---|---|---|
| H1 arranque reproducible/persistencia | Cumplida | Build/arranque en WSL/Docker, servicios saludables, backup/restore sin pérdida y Alembic head `0006_route_invalidation` |
| H2 datos/migraciones/integridad | Cumplida | Entidades con dominios, FKs, checks (UNKNOWN con NULL, NaN/Inf, geometría 4326, inmutabilidad); migración desde BD vacía y upgrade `0003`→`0006`; pruebas SQL directas de negativos y CRS |
| H3 API/contratos/worker | Cumplida | CRUD con idempotencia y huella de solicitud, snapshots con fingerprint, cola SQL durable con lease/reclamación, worker con verificación de hash y `MAX_ATTEMPTS`, 501 explícito en motores no implementados, seed demostrativo |
| H4 autenticación/roles/auditoría | Cumplida | Sesiones con Argon2id y CSRF, capacidades sin herencia, 401/403/409/422/429/501 verificados, auditoría persistente e inmutable, revocación, límite de intentos |
| Segregación SQL/BI | Cumplida | Lector BI SELECT sobre vista analytics y denegado en dominio/escritura; `sipre_app` denegado en borrar auditoría o alterar saldos; `sipre_worker` denegado en crear usuarios |
| Reconciliación SRS | Documentada | 103 requisitos y ocho objetivos mapeados; C01 resuelta por instrucción del usuario; C02/C03 documentadas como refinamientos técnicos |

Pruebas actuales: **51 aprobadas, 0 omitidas** con PostgreSQL/PostGIS real en Windows y Docker;
**19 checks E2E** HTTP sin dobles; **17 verificaciones Docker** con 0 fallos. Ruff y Compose config
pasan. Consulte [evidencia](phase9-test-evidence.md).

## Correcciones aplicadas en esta entrega

- Un único envoltorio de error `{"error":{"code":...,"correlation_id":...}}` para 401/403/404/409/
  422/429/501/503, sustituyendo el `{"detail":...}` por defecto de FastAPI.
- `GET /api/v1/users` (sólo ADMIN, sin `password_hash`) para completar la gestión RBAC.
- Higiene de sesiones: se eliminan sesiones expiradas del usuario en el siguiente login.
- Tests añadidos: conflicto `REVISION_CONFLICT` por revisión obsoleta, aislamiento de snapshot por
  emergencia, inmutabilidad SQL de `model.input_snapshots`, `SNAPSHOT_HASH_MISMATCH` y
  `MAX_ATTEMPTS` del worker, contrato de error 401/403/422, y login sin material de contraseña.
- Se detectó en Docker que el trigger de `route_candidate_edges` impedía la cascada al bloquear un
  arco. La migración incremental `0006_route_invalidation` permite invalidar candidatos, revoca
  el borrado directo de sus secuencias al rol de aplicación y conserva la inmutabilidad de UPDATE.
- La comprobación de readiness y las pruebas de head ahora exigen `0006`. Los verificadores
  Compose y HTTP están versionados en `scripts/`; documentación y trazabilidad reflejan H7.

## Decisiones aceptadas para el cierre

- La interpretación F9 = H1–H4, manteniendo la separación de hitos y sus puertas.
- Aceptar la interpretación documentada de F2/F3: `SIMULATED` fue elegido expresamente por el
  usuario; los cuatro estados de emergencia proceden del SRS; `DECISION_MAKER` es el identificador
  técnico de F6 para la capacidad del decisor, sin herencia de `ADMIN`.
- Con la evidencia presente, el usuario aprobó el cierre el 2026-10-17. Se registra
  `CLOSED_AFTER_APPROVAL` sin afirmar validación institucional o en terreno.

## Pendientes futuros que no bloquean por sí mismos F9

H7 GIS/rutas está implementado y probado, en `READY_FOR_REVIEW` por separado; D18 requiere
ratificación antes de integrar el motor. Siguen H5 AHP-TOPSIS; H6 OR-Tools SIPRE; H8 recomendaciones/decisiones/reservas atómicas;
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
- Este dictamen: `CLOSED_AFTER_APPROVAL` por decisión humana explícita.

F10/H5 queda autorizada por el mismo mensaje. H7 y D18 se revisan por separado; D06, D07 y D17
siguen pendientes antes de cerrar el motor. El prototipo no se certifica para uso real.
