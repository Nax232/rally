/* Interacciones logísticas y administración de alertas: demostración local únicamente. */
state.alerts = [
  {id:'AL-101',title:'Suministro de agua bajo umbral',type:'Necesidad',severity:'critical',zone:'Z-01',x:200,y:188,status:'Confirmada',created:'14:26'},
  {id:'AL-102',title:'Tránsito restringido',type:'Accesibilidad',severity:'high',zone:'Z-03',x:650,y:286,status:'En revisión',created:'14:11'},
  {id:'AL-103',title:'Reporte de infraestructura',type:'Infraestructura',severity:'medium',zone:'Z-04',x:820,y:250,status:'Nueva',created:'13:57'},
  {id:'AL-104',title:'Solicitud de atención médica',type:'Salud',severity:'critical',zone:'Z-02',x:505,y:180,status:'Atendida',created:'13:42'}
];
state.transports = [
  {id:'T-01',name:'Ambulancia',code:'A-03',zone:'Z-04',status:'En ruta',progress:.28,color:'#49a7ff'},
  {id:'T-02',name:'Camión de suministros',code:'C-12',zone:'Z-01',status:'En ruta',progress:.54,color:'#f5b84b'},
  {id:'T-03',name:'Camioneta de apoyo',code:'V-07',zone:'Z-03',status:'En espera',progress:0,color:'#a88bff'}
];
state.alertPlacement = false;
state.pendingAlertPoint = null;

const _operationsMapMarkup = mapMarkup;
mapMarkup = function(){
  let html=_operationsMapMarkup();
  const at=html.lastIndexOf('</svg>');
  if(at>=0)html=html.slice(0,at)+transportAndAlertOverlay()+html.slice(at);
  html=html.replace('<button class="tool-chip active">Red vial</button>', '<button class="tool-chip active">Red vial</button><button class="tool-chip" data-action="add-alert">＋ Crear alerta</button><button class="tool-chip" data-action="dispatch-transport">＋ Despachar transporte</button>');
  return html;
};

function routeForTransport(unit){return roadRoute(BASE_POINT,ALERT_POINTS[unit.zone]||ALERT_POINTS['Z-04']);}
function pointAlong(points,fraction){
  if(!points.length)return{x:0,y:0};
  const lengths=[];let total=0;
  for(let i=1;i<points.length;i++){const d=pointDistance(points[i-1],points[i]);lengths.push(d);total+=d;}
  if(total<=0)return points[0];let left=total*clamp(fraction,0,1);
  for(let i=0;i<lengths.length;i++){if(left<=lengths[i]){const t=lengths[i]?left/lengths[i]:0;return{x:points[i].x+(points[i+1].x-points[i].x)*t,y:points[i].y+(points[i+1].y-points[i].y)*t};}left-=lengths[i];}
  return points.at(-1);
}
function transportAndAlertOverlay(){
  const alertMarks=state.alerts.filter(a=>a.status!=='Cerrada').map(a=>`<g class="live-alert-pin sev-${esc(a.severity)}" data-alert-pin="${esc(a.id)}" tabindex="0" role="button" aria-label="Alerta ${esc(a.id)}: ${esc(a.title)}, ${esc(a.status)}"><circle class="alert-pin-halo" cx="${a.x}" cy="${a.y}" r="10"/><circle class="alert-pin-core" cx="${a.x}" cy="${a.y}" r="5"/><text x="${a.x+9}" y="${a.y-8}">${esc(a.id.slice(-2))}</text><title>${esc(a.title)} · ${esc(a.status)}</title></g>`).join('');
  const routes=state.transports.filter(t=>t.status==='En ruta'||t.status==='Pausado').map(t=>{const r=routeForTransport(t);return r.points.length?`<polyline class="transport-route ${t.status==='Pausado'?'paused':''}" stroke="${t.color}" points="${pointString(r.points)}"/>`:'';}).join('');
  const units=state.transports.filter(t=>t.status==='En ruta'||t.status==='Pausado').map(t=>{const r=routeForTransport(t),p=pointAlong(r.points,t.progress);return `<g class="transport-pin ${t.status==='Pausado'?'paused':''}" data-transport-pin="${esc(t.id)}" transform="translate(${p.x} ${p.y})"><circle r="9" fill="#091421" stroke="${t.color}" stroke-width="2.5"/><text y="3.5" fill="${t.color}">${t.name.startsWith('Ambulancia')?'✚':t.name.startsWith('Camión')?'▰':'●'}</text><title>${esc(t.name)} ${esc(t.code)} · ${esc(t.status)} · ${zone(t.zone).name}</title></g>`;}).join('');
  return `${routes}${alertMarks}${units}`;
}

const _operationsMapView = mapView;
mapView=function(){
  const rows=state.alerts.map(a=>`<tr><td><strong>${esc(a.id)} · ${esc(a.title)}</strong><small style="display:block;color:#7489a3;margin-top:4px">${esc(a.type)} · ${esc(zone(a.zone).name)} · ${esc(a.created)}</small></td><td>${riskTag(a.severity)}</td><td><span class="tag ${a.status==='Atendida'||a.status==='Cerrada'?'green':a.status==='En revisión'?'orange':'blue'}">${esc(a.status)}</span></td><td><button class="tool-chip" data-action="alert-next:${esc(a.id)}" ${a.status==='Cerrada'?'disabled':''}>${a.status==='Nueva'?'Revisar':a.status==='En revisión'?'Confirmar':a.status==='Confirmada'?'Atender':a.status==='Atendida'?'Cerrar':'Cerrada'}</button></td></tr>`).join('');
  const units=state.transports.map(t=>`<div class="transport-card"><div class="transport-ident"><i style="--unit-color:${t.color}">${t.name.startsWith('Ambulancia')?'✚':t.name.startsWith('Camión')?'▰':'●'}</i><div><strong>${esc(t.name)} · ${esc(t.code)}</strong><small>Destino: ${esc(zone(t.zone).name)} · ${t.status==='En ruta'?`${Math.round(t.progress*100)}% del trayecto`:esc(t.status)}</small></div></div><div class="transport-actions">${t.status==='En ruta'?btn('Pausar','','transport-pause:'+esc(t.id)):t.status==='Pausado'?btn('Reanudar','primary','transport-resume:'+esc(t.id)):btn(t.status==='En destino'?'Nuevo destino':'Despachar','primary','transport-dispatch:'+esc(t.id))}</div></div>`).join('');
  return `${layoutHead('CAPAS TERRITORIALES','Mapa operacional','Red vial de referencia · alertas y desplazamientos demostrativos',`<span class="tag blue">Todos los cambios son simulados</span>`)}<div class="grid dashboard-grid">${mapMarkup()}${selectedZoneCard()}</div><div class="operations-grid"><section class="card operations-panel"><div class="card-head"><div><h3>Transportes y desplazamientos</h3><small>Movimiento visual sobre rutas calculadas con A*</small></div><span class="tag blue">${state.transports.filter(t=>t.status==='En ruta').length} en ruta</span></div><div class="transport-list">${units}</div><p class="operations-note">El despacho inicia sólo la simulación local del vehículo. No se transmite una orden ni se contacta a operadores.</p></section><section class="card table-card operations-panel"><div class="card-head"><div><h3>Administración de alertas</h3><small>Nueva → En revisión → Confirmada → Atendida → Cerrada</small></div><button class="tool-chip" data-action="add-alert">＋ Crear en mapa</button></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Alerta y ubicación</th><th>Prioridad</th><th>Estado</th><th>Gestión</th></tr></thead><tbody>${rows}</tbody></table></div><p class="operations-note">Las alertas nuevas se ubican haciendo clic en un punto del mapa después de activar «Crear alerta».</p></section></div><div class="card table-card" style="margin-top:15px"><div class="card-head"><h3>Rutas y restricciones de accesibilidad</h3><span class="tag blue">Red demostrativa · revisión 14:20</span></div><table class="data-table"><thead><tr><th>Tramo</th><th>Estado</th><th>Motivo</th><th>Última observación</th><th>Alternativa</th></tr></thead><tbody><tr><td><strong>Cll. Riberas · sector norte</strong></td><td>${riskTag('critical')}</td><td>Bloqueo vial simulado</td><td>14:11 · reporte demostrativo</td><td>Recalcular por la red A*</td></tr><tr><td><strong>Diagonal Alba · cruce Av. Central</strong></td><td>${riskTag('high')}</td><td>Acceso con demora estimada</td><td>13:48 · reporte demostrativo</td><td>Ruta alternativa calculada con A*</td></tr><tr><td><strong>Av. Marina · sector centro</strong></td><td>${riskTag('low')}</td><td>Tramo habilitado en el escenario</td><td>13:22 · estado simulado</td><td>—</td></tr></tbody></table></div>`;
};

const _operationsHandleAction=window.handleAction;
window.handleAction=function(action){
  if(action==='add-alert'){state.alertPlacement=true;toast('Seleccione un punto del mapa','Se abrirá el formulario para registrar la alerta');render();document.querySelector('.source-map-canvas')?.classList.add('placing-alert');return;}
  if(action==='dispatch-transport'){openTransportForm();return;}
  if(action.startsWith('transport-pause:')||action.startsWith('transport-resume:')){const [verb,id]=action.split(':');const t=state.transports.find(x=>x.id===id);if(!t)return;t.status=verb==='transport-pause'?'Pausado':'En ruta';auditTransport(`${t.code} ${t.status.toLowerCase()}`);render();return;}
  if(action.startsWith('transport-dispatch:')){openTransportForm(action.split(':')[1]);return;}
  if(action.startsWith('alert-next:')){const a=state.alerts.find(x=>x.id===action.split(':')[1]);if(!a)return;const next={Nueva:'En revisión','En revisión':'Confirmada',Confirmada:'Atendida',Atendida:'Cerrada'};if(!next[a.status])return;a.status=next[a.status];state.notifications=state.alerts.filter(x=>x.status==='Nueva'||x.status==='En revisión').length;a.created=new Date().toLocaleTimeString('es-CL',{hour:'2-digit',minute:'2-digit'});state.audit.unshift([a.created,'María Rojas',`${a.id}: alerta ${a.status.toLowerCase()}`,'Gestión de alerta']);render();toast('Estado de alerta actualizado',`${a.id} · ${a.status}`);return;}
  if(action==='create-alert'){const title=$('#alertTitle')?.value.trim(),type=$('#alertType')?.value,severity=$('#alertSeverity')?.value,zoneId=$('#alertZone')?.value;if(!title||!state.pendingAlertPoint){toast('Falta información','Indica un asunto y selecciona un punto del mapa');return;}const id=`AL-${String(101+state.alerts.length).padStart(3,'0')}`,time=new Date().toLocaleTimeString('es-CL',{hour:'2-digit',minute:'2-digit'});state.alerts.unshift({id,title,type,severity,zone:zoneId,x:state.pendingAlertPoint.x,y:state.pendingAlertPoint.y,status:'Nueva',created:time});state.pendingAlertPoint=null;state.alertPlacement=false;state.notifications++;state.audit.unshift([time,'María Rojas',`${id}: nueva alerta · ${title}`,'Gestión de alerta']);closeModal();render();toast('Alerta creada',`${id} · Nueva · requiere revisión humana`);return;}
  if(action==='save-transport-dispatch'){const id=$('#transportId')?.value,t=state.transports.find(x=>x.id===id),zoneId=$('#transportZone')?.value;if(!t||!zoneId)return;t.zone=zoneId;t.progress=0;t.status='En ruta';auditTransport(`${t.code} inicia desplazamiento a ${zone(zoneId).name}`);closeModal();render();toast('Desplazamiento simulado iniciado',`${t.code} · ruta A* hacia ${zone(zoneId).name}`);return;}
  return _operationsHandleAction(action);
};
function auditTransport(text){const time=new Date().toLocaleTimeString('es-CL',{hour:'2-digit',minute:'2-digit',second:'2-digit'});state.audit.unshift([time,'Operador DEMO',text,'Movimiento simulado']);}
function openTransportForm(unitId=''){
  const available=state.transports.filter(t=>t.status==='En espera'||t.status==='En destino'||t.status==='Pausado');
  const options=(unitId?state.transports.filter(t=>t.id===unitId):available).map(t=>`<option value="${esc(t.id)}">${esc(t.name)} · ${esc(t.code)}</option>`).join('');
  if(!options){toast('No hay transportes disponibles','Agrega una unidad al escenario antes de despachar');return;}
  openModal(`<div class="modal-head"><h2>Despachar transporte simulado</h2><button class="modal-close" data-close>×</button></div><div class="modal-body"><span class="tag orange">ACCIÓN DE DEMOSTRACIÓN</span><div class="form-grid" style="margin-top:15px"><div class="form-field full"><label>Unidad</label><select id="transportId">${options}</select></div><div class="form-field full"><label>Destino</label><select id="transportZone">${state.zones.map(z=>`<option value="${z.id}" ${z.id===state.selectedZone?'selected':''}>${z.id} · ${esc(z.name)}</option>`).join('')}</select></div></div><p class="operations-note">El transporte se moverá visualmente desde la base A1 siguiendo la ruta A*. Esto no genera una orden operacional real.</p></div><div class="modal-footer">${btn('Cancelar','','close-modal')}${btn('Iniciar desplazamiento','primary','save-transport-dispatch')}</div>`);
}

document.addEventListener('click',event=>{
  const alertPin=event.target.closest('[data-alert-pin]');
  if(alertPin){const a=state.alerts.find(x=>x.id===alertPin.dataset.alertPin);if(a){state.selectedZone=a.zone;render();toast(`${a.id} · ${a.title}`,`${a.status} · ${zone(a.zone).name}`);}return;}
  if(!state.alertPlacement)return;
  const svg=event.target.closest('svg.source-map');if(!svg)return;
  event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();
  const box=svg.getBoundingClientRect(),x=clamp((event.clientX-box.left)*1000/box.width,5,995),y=clamp((event.clientY-box.top)*620/box.height,5,615);
  state.pendingAlertPoint={x:Math.round(x),y:Math.round(y)};state.alertPlacement=false;
  openModal(`<div class="modal-head"><h2>Registrar alerta territorial</h2><button class="modal-close" data-close>×</button></div><div class="modal-body"><span class="tag blue">DATOS SIMULADOS · ${x.toFixed(0)}, ${y.toFixed(0)}</span><div class="form-grid" style="margin-top:15px"><div class="form-field full"><label>Descripción</label><input id="alertTitle" maxlength="90" placeholder="Ej. Puente con acceso interrumpido"></div><div class="form-field"><label>Tipo</label><select id="alertType"><option>Accesibilidad</option><option>Infraestructura</option><option>Necesidad</option><option>Salud</option><option>Seguridad</option><option>Otro</option></select></div><div class="form-field"><label>Prioridad inicial</label><select id="alertSeverity"><option value="high">Alta</option><option value="critical">Crítica</option><option value="medium">Media</option><option value="low">Baja</option></select></div><div class="form-field full"><label>Zona asociada</label><select id="alertZone">${state.zones.map(z=>`<option value="${z.id}" ${z.id===state.selectedZone?'selected':''}>${z.id} · ${esc(z.name)}</option>`).join('')}</select></div></div><p class="operations-note">La alerta quedará en estado «Nueva» hasta que una persona la revise.</p></div><div class="modal-footer">${btn('Cancelar','','close-modal')} ${btn('Guardar alerta','primary','create-alert')}</div>`);
},true);

function updateMovingUnits(){
  let completed=false;
  for(const t of state.transports){if(t.status!=='En ruta')continue;t.progress=Math.min(1,t.progress+.012);if(t.progress>=1){t.status='En destino';auditTransport(`${t.code} llegó a ${zone(t.zone).name}`);completed=true;}}
  document.querySelectorAll('[data-transport-pin]').forEach(el=>{const t=state.transports.find(x=>x.id===el.dataset.transportPin);if(!t||t.status!=='En ruta')return;const p=pointAlong(routeForTransport(t).points,t.progress);el.setAttribute('transform',`translate(${p.x} ${p.y})`);});
  if(completed){render();toast('Transporte llegó a destino','El escenario se actualizó; sin operación real');}
}
setInterval(updateMovingUnits,700);

const _operationsRender=window.render;
window.render=function(){_operationsRender();document.querySelector('.source-map-canvas')?.classList.toggle('placing-alert',state.alertPlacement);};
render();
