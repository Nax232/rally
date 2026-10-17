# Fase 10 — Estado de implementación

Inicio autorizado por el usuario el 2026-10-17 tras cerrar Fase 9. Alcance: Hito 5 del plan
F8, priorización AHP-TOPSIS F4 sobre datos `SIMULATED`. **Estado actual: IN_PROGRESS;
cierre bloqueado por registro de perfiles F6 y ratificación del perfil DEMO**.
Esta página no declara cierre ni certificación operacional.

Entregado hasta ahora:

- Núcleo puro F4 con AHP geométrico, RI8=1.41, CR≤0.10, pesos DEMO, TOPSIS anclado,
  bandas, intervalos con C8 fijo, contribuciones de distancia y contrafactual no aditivo.
- Adaptador de reportes/necesidades sintéticos a C1…C8, con proveniencia, fechas, `NULL`
  distinto de cero y banderas de verificación.
- Migraciones incrementales `0007_prioritization` y `0008_simulated_assistance`: corridas,
  asistencia, resultados, factores, FK por
  emergencia, inmutabilidad y vistas BI de sólo lectura. API con cola durable, ámbito y
  capacidad `jobs`; worker transaccional desde snapshot y perfil versionado.
- Perfil DEMO propuesto y sujeto a revisión en [phase10-demo-profile.md](phase10-demo-profile.md).

Evidencia observada al 2026-10-17: migración `0006`→`0008` correcta en PostgreSQL/PostGIS
local; suite `scripts/local-runtime.py test`: **69 passed, 4 warnings**. La suite cubre
fixture F4, normalización sintética, endpoint/worker, persistencia, inmutabilidad y
segregación del lector BI. Docker compiló imágenes F10, aplicó head `0008`, pasó
17 verificaciones de infraestructura, **69 pruebas en contenedor** y 21 checks HTTP E2E.
Ruff no reportó errores y `uv pip check` verificó 50 paquetes compatibles.

Pendientes antes de revisión de cierre: ratificación numérica del perfil DEMO D06,
registro/aprobación de perfiles por ID exigido por F6 y RF-035…RF-038, y revisión H7/D18.
La migración propuesta de perfiles no fue aplicada tras rechazo de permisos; véase
[phase10-profile-registry-proposal.md](phase10-profile-registry-proposal.md). C5 cruza
reporte y candidato verificado del mismo snapshot y marca contradicción, sin deducir
aislamiento cuando faltan candidatos. H6 optimización y decisiones humanas H8 pertenecen
a fases posteriores; no se implementan para declarar F10 completa.
