/* Extensión del flujo de pathfinding y aprobación humana para la demo. */
function refreshMapLabels(){
  const map=document.querySelector('.map-canvas'); if(!map||map.classList.contains('source-map-canvas'))return;
  let labels=[...map.querySelectorAll('.map-label')];
  if(!labels.length){
    [['VIÑA DEL MAR',7,11],['Av. San Martín',23,24],['Camino Sausalito',47,32],['Av. Libertad',30,54],['1 Norte',53,57],['Camino Troncal',62,85]].forEach(([name,left,top])=>{const el=document.createElement('span');el.className='map-label street-label';el.style.left=`${left}%`;el.style.top=`${top}%`;el.textContent=name;map.appendChild(el);});
  } else ['VIÑA DEL MAR','SAUSALITO','MIRAFLORES ALTO','CHORRILLOS'].forEach((name,i)=>{if(labels[i])labels[i].textContent=name;});
}
refreshMapLabels();
const _sipreRenderWithMap = window.render;
window.render = function(){_sipreRenderWithMap();refreshMapLabels();};

function openActionPlan(){
  state.actionPlan.routeZone=state.selectedZone;
  const r=routeForZone(state.actionPlan.routeZone), z=zone(state.actionPlan.routeZone);
  openModal(`<div class="modal-head"><h2>Plan de acción de emergencia</h2><button class="modal-close" data-close>×</button></div><div class="modal-body"><span class="tag orange">PENDIENTE DE APROBACIÓN</span><p style="margin-top:12px">${esc(state.actionPlan.emergency)} · plan ${esc(state.actionPlan.createdAt)} · datos simulados.</p><div class="action-plan"><div class="plan-step"><b>01</b><div><strong>Confirmar zona prioritaria</strong><span>${esc(z.name)} · ${esc(z.need)} · score ${z.score.toFixed(2)}</span></div><i>✓</i></div><div class="plan-step"><b>02</b><div><strong>Preparar recurso recomendado</strong><span>${esc(z.need)} · inventario y capacidad verificados en demo</span></div><i>✓</i></div><div class="plan-step"><b>03</b><div><strong>Usar ruta vial de menor distancia</strong><span>Base A1 → ${r.streets.join(' → ')} → ${esc(z.name)} · ${r.distance.toFixed(1)} u · ${r.nodes.length} intersecciones · A*</span></div><i>✓</i></div><div class="plan-step pending"><b>04</b><div><strong>Decisión del supervisor</strong><span>Aprobar, rechazar o solicitar ajustes</span></div><i>…</i></div></div><div class="explain" style="margin:14px 0 0"><p>La aprobación registra una decisión humana y deja el plan listo para ejecución manual. SIPRE no despacha vehículos ni modifica inventario automáticamente.</p></div></div><div class="modal-footer">${btn('Rechazar','danger','reject-action-plan')}${btn('Solicitar ajustes','','reject-action-plan')}${btn('Aprobar plan','success','approve-action-plan')}</div>`);
}
const _sipreBaseHandleAction = window.handleAction;
window.handleAction = function(action){
  if(action==='open-action-plan'||action==='recalculate-path'||action==='approve-action-plan'||action==='reject-action-plan'){
    if(action==='recalculate-path'){const r=routeForZone(state.selectedZone);state.audit.unshift(['14:32:08','SIPRE DEMO',`Ruta A* recalculada para ${state.selectedZone}`,'Simulado']);toast('Ruta recalculada',`${r.distance.toFixed(1)} u · ${r.nodes.length} intersecciones · red vial de referencia`);render();return;}
    if(action==='open-action-plan'){openActionPlan();return;}
    if(action==='approve-action-plan'){state.actionPlan.status='Aprobado por supervisor';state.audit.unshift(['14:32:08',state.actionPlan.supervisor,'Plan de acción aprobado','Decisión humana']);closeModal();toast('Plan aprobado por supervisor','La recomendación queda lista para ejecución manual');render();return;}
    state.actionPlan.status='Requiere ajustes';state.audit.unshift(['14:32:08',state.actionPlan.supervisor,'Plan de acción rechazado para ajustes','Decisión humana']);closeModal();toast('Plan enviado a ajustes','No se ejecutó ninguna operación');render();return;
  }
  return _sipreBaseHandleAction(action);
};
