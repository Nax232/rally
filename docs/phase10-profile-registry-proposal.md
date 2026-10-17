# Fase 10 — propuesta de registro de perfiles F6

Estado: **propuesta no aplicada**. La ejecución de una migración `0009` en PostgreSQL local
fue rechazada por la revisión de permisos del entorno el 2026-10-17. Se retiró el archivo
de la cadena activa de Alembic para que un arranque futuro no aplique una migración no
validada. La base probada permanece en `0008_simulated_assistance`.

F6 §4.1 y §6 requiere identidades separadas para perfiles de criterios, AHP y
clasificación, y que la solicitud de una corrida refiera a sus versiones. La primera
implementación F10 guarda un perfil DEMO completo, su versión y SHA-256 dentro de cada
`model.priority_runs`, lo que preserva reconstrucción, pero aún no cubre plenamente
RF-035…RF-038 ni el contrato de perfil por ID de F6. No debe declararse F10 cerrada
antes de resolver esta brecha.

## Migración propuesta

- `model.criteria_profiles(criteria_profile_id,version,config,hash,approved,origin,
  created_by,approved_by,created_at,approved_at)`.
- `model.ahp_profiles(ahp_profile_id,version,pairwise_matrix,weights,ci,cr,hash,
  approved,origin,created_by,approved_by,created_at,approved_at)` con `cr≤0.10`.
- `model.classification_profiles(classification_profile_id,version,config,hash,
  approved,origin,created_by,approved_by,created_at,approved_at)`.
- FKs opcionales en `model.priority_runs` para conservar corridas históricas de `0007`;
  nuevas corridas exigirían los tres IDs. La copia inmutable del perfil y hash seguiría
  en cada corrida.
- Versiones únicas y append-only. La única actualización permitida sería pasar un
  perfil propuesto a `approved=true`, registrando `approved_by` y fecha, con comprobación
  de rol `ADMIN` también en la base. ADMIN aprobaría **perfiles**, jamás decisiones
  operacionales. Un perfil usado no cambiaría parámetros retroactivamente.
- API `GET/POST /api/v1/profiles/{criteria,ahp,classification}` y acción de aprobación
  separada. AHP usaría el cálculo F4 y rechazaría CR>0.10; los perfiles DEMO sin revisión
  seguirían etiquetados `SYNTHETIC_REVIEW_PENDING` y no aparentarían validación experta.

## Puertas de validación

1. Revisar las tres entidades y el flujo de aprobación contra F4/F6 y la decisión humana
   del perfil DEMO.
2. Aplicar una migración incremental comprobada sobre la base local aislada, desde
   `0008` y desde una base vacía; sin borrar corridas existentes.
3. Probar RBAC (ANALYST propone, ADMIN aprueba perfiles), CR inválido, perfiles ausentes,
   IDs cruzados, inmutabilidad, huella y replay histórico.
4. Repetir suite completa, Docker, upgrade y E2E antes de proponer cierre F10.

Ninguna acción de aprobación de perfil debe aprobar una recomendación, reservar stock ni
generar una orden de despacho.
