const statusText={running:'▶ Em execução',waiting:'⏸ Aguardando limite',finished:'✓ Concluído',failed:'✗ Falhou',stopped:'⏹ Encerrado',done:'✓ Concluída',incomplete:'! Incompleta',skipped:'– Pulada',pending:'· Pendente'};
const engineLabels={codex:'Codex',antigravity:'Antigravity',claude:'Claude',opencode:'OpenCode'};
const $=s=>document.querySelector(s);
let selected='current', logOffsets=new Map(), followLogs=true;
let catalogData={configured_engines:[],engines:{},flat:[]};
let enabledEngines=new Set();
let priorityQueue=[];
let loadedPhases=[];
let selectedPhases=new Set();

function esc(value){return String(value??'—').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}
function status(value){return `<span class="${esc(value)}">${statusText[value]||esc(value)}</span>`}
function count(state){let total=0,done=0;state.phases.forEach(p=>p.tasks.forEach(t=>{total++;if(t.status==='done')done++}));return{total,done}}
function bar(label,done,total){const p=total?Math.round(done*100/total):0;return `<div class="bar-row"><span>${label}</span><div class="bar" role="progressbar" aria-label="${label}" aria-valuenow="${p}" aria-valuemin="0" aria-valuemax="100"><i style="width:${p}%"></i></div><span>${p}%</span></div>`}
async function postJson(url,value){const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});const data=await res.json();if(!res.ok)throw new Error(data.message||data.error||'Falha na operação');return data}

function parseRoute(route){
  const idx=String(route).indexOf(':');
  if(idx>0){return{engine:route.slice(0,idx),id:route.slice(idx+1)}}
  return{engine:'',id:route};
}

function modelLabelForRoute(route){
  const found=(catalogData.flat||[]).find(m=>m.route===route);
  if(found)return `${found.label} (${found.id})`;
  const parsed=parseRoute(route);
  return parsed.id||route;
}

function renderEnginesBar(){
  const barEl=$('#engines-bar');
  const configured=catalogData.configured_engines||[];
  if(!configured.length){
    barEl.innerHTML='<span class="muted">Nenhuma engine configurada.</span>';
    return;
  }
  barEl.innerHTML=configured.map(eng=>{
    const info=catalogData.engines?.[eng]||{};
    const countModels=(info.models||[]).length;
    const checked=enabledEngines.has(eng)?'checked':'';
    const activeCls=enabledEngines.has(eng)?'active':'';
    const cliWarn=info.installed?'':' · CLI ausente';
    return `<label class="engine-chip ${activeCls}"><input type="checkbox" data-engine="${esc(eng)}" ${checked}> <span>${esc(engineLabels[eng]||eng)}</span> <span class="muted">(${countModels} modelos${cliWarn})</span></label>`;
  }).join('');

  barEl.querySelectorAll('input[data-engine]').forEach(cb=>{
    cb.addEventListener('change',()=>{
      const eng=cb.dataset.engine;
      if(cb.checked)enabledEngines.add(eng);
      else enabledEngines.delete(eng);
      renderEnginesBar();
      renderModelPickers();
    });
  });
}

function renderModelPickers(){
  const picker=$('#model-picker');
  const verifySel=$('#verify-model-select');
  const oldPicker=picker.value;
  const oldVerify=verifySel.value;

  picker.replaceChildren();
  verifySel.replaceChildren(new Option('Seguir mesma fila de prioridade da implementação',''));

  const activeEngines=[...enabledEngines];
  let totalAdded=0;

  activeEngines.forEach(eng=>{
    const items=catalogData.engines?.[eng]?.models||[];
    if(!items.length)return;
    const grp1=document.createElement('optgroup');
    grp1.label=`${engineLabels[eng]||eng} (${catalogData.engines[eng].source||'CLI'})`;
    const grp2=document.createElement('optgroup');
    grp2.label=grp1.label;

    items.forEach(item=>{
      const text=item.label&&item.label!==item.id?`${item.label} [${item.id}]`:item.id;
      grp1.appendChild(new Option(text,item.route));
      grp2.appendChild(new Option(`${engineLabels[eng]||eng} · ${text}`,item.route));
      totalAdded++;
    });
    picker.appendChild(grp1);
    verifySel.appendChild(grp2);
  });

  if(!totalAdded){
    picker.appendChild(new Option('Nenhum modelo descoberto para as engines ativas',''));
  }else if([...picker.options].some(o=>o.value===oldPicker)){
    picker.value=oldPicker;
  }
  if([...verifySel.options].some(o=>o.value===oldVerify)){
    verifySel.value=oldVerify;
  }
}

function renderPriorityQueue(){
  const list=$('#priority-queue');
  if(!priorityQueue.length){
    list.innerHTML='<li class="muted">Nenhum modelo na fila. Selecione um modelo acima e clique em "+ Adicionar".</li>';
    return;
  }
  list.innerHTML=priorityQueue.map((route,idx)=>{
    const {engine}=parseRoute(route);
    const label=modelLabelForRoute(route);
    return `<li class="priority-item" data-index="${idx}">
      <span class="priority-rank">${idx+1}º</span>
      <span class="engine-badge ${esc(engine)}">${esc(engineLabels[engine]||engine||'CLI')}</span>
      <span class="priority-label" title="${esc(route)}">${esc(label)}</span>
      <span class="priority-actions">
        <button type="button" data-act="up" ${idx===0?'disabled':''} title="Subir prioridade">↑</button>
        <button type="button" data-act="down" ${idx===priorityQueue.length-1?'disabled':''} title="Descer prioridade">↓</button>
        <button type="button" data-act="remove" title="Remover da fila">✕</button>
      </span>
    </li>`;
  }).join('');

  list.querySelectorAll('.priority-item').forEach(li=>{
    const idx=Number(li.dataset.index);
    li.querySelector('[data-act="up"]')?.addEventListener('click',()=>{
      if(idx<=0)return;
      [priorityQueue[idx-1],priorityQueue[idx]]=[priorityQueue[idx],priorityQueue[idx-1]];
      renderPriorityQueue();
    });
    li.querySelector('[data-act="down"]')?.addEventListener('click',()=>{
      if(idx>=priorityQueue.length-1)return;
      [priorityQueue[idx+1],priorityQueue[idx]]=[priorityQueue[idx],priorityQueue[idx+1]];
      renderPriorityQueue();
    });
    li.querySelector('[data-act="remove"]')?.addEventListener('click',()=>{
      priorityQueue.splice(idx,1);
      renderPriorityQueue();
    });
  });
}

function renderPhasesChecklist(){
  const box=$('#phases-checklist');
  if(!loadedPhases.length){
    box.innerHTML='<p class="muted">Nenhuma fase encontrada neste documento.</p>';
    return;
  }
  box.innerHTML=loadedPhases.map(p=>{
    const checked=selectedPhases.has(p.number)?'checked':'';
    const badge=p.done?'<span class="done">✓ Concluída</span>':'<span class="pending">· Pendente</span>';
    return `<label class="phase-option">
      <input type="checkbox" data-phase="${p.number}" ${checked}>
      <span><b>F${p.number}</b> · ${esc(p.title)}</span>
      <span class="phase-meta">${p.tasks_count} tasks · ${badge}</span>
    </label>`;
  }).join('');

  box.querySelectorAll('input[data-phase]').forEach(cb=>{
    cb.addEventListener('change',()=>{
      const num=Number(cb.dataset.phase);
      if(cb.checked)selectedPhases.add(num);
      else selectedPhases.delete(num);
    });
  });
}

async function loadPhasesForInput(inputPath){
  const box=$('#phases-checklist');
  if(!inputPath){
    loadedPhases=[];
    selectedPhases.clear();
    box.innerHTML='<p class="muted">Selecione um documento de fases acima.</p>';
    return;
  }
  box.innerHTML='<p class="muted">Lendo fases do documento…</p>';
  try{
    const data=await fetch(`/api/v1/phases?input=${encodeURIComponent(inputPath)}`,{cache:'no-store'}).then(r=>r.json());
    if(data.error)throw new Error(data.error);
    loadedPhases=data.phases||[];
    const pending=loadedPhases.filter(p=>!p.done).map(p=>p.number);
    selectedPhases=new Set(pending.length?pending:loadedPhases.map(p=>p.number));
    renderPhasesChecklist();
  }catch(err){
    loadedPhases=[];
    selectedPhases.clear();
    box.innerHTML=`<p class="failed">Erro ao ler fases: ${esc(err.message)}</p>`;
  }
}

async function loadModels(forceRefresh=false){
  try{
    const url=forceRefresh?'/api/v1/models?refresh=1':'/api/v1/models';
    catalogData=await fetch(url,{cache:'no-store'}).then(r=>r.json());
    const configured=catalogData.configured_engines||[];
    if(!enabledEngines.size){
      configured.forEach(e=>enabledEngines.add(e));
    }
    if(!priorityQueue.length && (catalogData.flat||[]).length){
      // Se nenhuma fila salva existir ainda, sugere o primeiro modelo descoberto de cada engine configurada
      configured.forEach(eng=>{
        const first=catalogData.engines?.[eng]?.models?.[0];
        if(first&&!priorityQueue.includes(first.route))priorityQueue.push(first.route);
      });
    }
    renderEnginesBar();
    renderModelPickers();
    renderPriorityQueue();
  }catch(err){
    $('#notice').textContent=`Falha ao descobrir modelos: ${err.message}`;
  }
}

async function loadControls(){
  try{
    const [config,inputs]=await Promise.all([
      fetch('/api/v1/config',{cache:'no-store'}).then(r=>r.json()),
      fetch('/api/v1/inputs',{cache:'no-store'}).then(r=>r.json())
    ]);
    $('#implementation-limit').value=config.limits?.implementation_minutes??30;
    $('#verification-limit').value=config.limits?.verification_minutes??5;
    $('#idle-limit').value=config.limits?.idle_warning_minutes??5;

    const savedQueue=config.models?.priority_queue;
    if(Array.isArray(savedQueue)&&savedQueue.length){
      priorityQueue=[...savedQueue];
    }

    await loadModels(false);

    const savedVerifyQueue=config.models?.verify_queue;
    if(Array.isArray(savedVerifyQueue)&&savedVerifyQueue.length){
      const vSel=$('#verify-model-select');
      if(![...vSel.options].some(o=>o.value===savedVerifyQueue[0])){
        vSel.appendChild(new Option(savedVerifyQueue[0],savedVerifyQueue[0]));
      }
      vSel.value=savedVerifyQueue[0];
    }

    const inputEl=$('#input');
    const available=inputs.inputs||[];
    inputEl.replaceChildren(new Option('Selecione um input',''),...available.map(v=>new Option(v,v)));

    const urlInput=new URLSearchParams(window.location.search).get('input');
    if(urlInput&&available.includes(urlInput)){
      inputEl.value=urlInput;
    }else if(available.length===1){
      inputEl.value=available[0];
    }
    if(inputEl.value){
      await loadPhasesForInput(inputEl.value);
    }
  }catch(error){
    $('#notice').textContent=`Falha ao carregar configuração: ${error.message}`;
  }
}

function currentConfig(){
  const n=id=>Math.max(0,Math.min(240,Number.parseInt($(id).value,10)||0));
  const verifyVal=$('#verify-model-select').value;
  return{
    models:{
      implementation:'',
      verification:'',
      priority_queue:[...priorityQueue],
      verify_queue:verifyVal?[verifyVal]:[]
    },
    limits:{
      implementation_minutes:n('#implementation-limit'),
      verification_minutes:n('#verification-limit'),
      idle_warning_minutes:n('#idle-limit')
    }
  };
}

function render(state){
  const run=state.run||{meta:{}};
  const m=run.meta||{}, phases=state.phases||[];
  const pc={total:phases.length,done:phases.filter(p=>p.status==='done'||p.status==='skipped').length}, tc=count(state);
  $('#notice').textContent=state.run?'':'Nenhuma execução encontrada neste repositório.';
  $('#summary').innerHTML=`<div><b>Projeto:</b> ${esc(m.project)}<br><b>Engine:</b> ${esc(m.engine)}<br><b>Modelo:</b> ${esc(m.model)}<br><b>Perfil:</b> ${esc(m.profile)}<br><b>Status:</b> ${status(m.status||'pending')}</div><div><b>Run:</b> ${esc(run.id||m.run)}<br><b>PID:</b> ${esc(m.pid)}<br><b>Failovers:</b> ${esc(m.failovers||'0')}<br><b>Duração:</b> ${duration(m.started,m.ended)}</div>`;
  $('#progress').innerHTML=bar('Fases',pc.done,pc.total)+bar('Tasks',tc.done,tc.total)+`<p class="muted">Teste: ${esc(m.test_cmd)}</p>`;
  const current=phases.find(p=>p.number===m.phase_cur)||{};
  $('#current').innerHTML=`<dt>Fase</dt><dd>${current.number?`${current.number} · ${esc(current.title)}`:'—'}</dd><dt>Ciclo</dt><dd>${esc(m.cycle)}/${esc(m.cycle_max)}</dd><dt>Gate</dt><dd>${esc(m.gate)}</dd><dt>Atividade</dt><dd>${esc(m.activity)}</dd><dt>Último erro</dt><dd class="failed">${esc(m.last_error)}</dd>`;
  $('#tasks').innerHTML=phases.flatMap(p=>{const phase=`<tr class="phase ${p.status==='running'?'active':''}"><td>F${esc(p.number)}</td><td>${esc(p.title)}</td><td>${status(p.status)}</td><td>${esc(p.attempt==='0'?'–':p.attempt)}</td><td class="gates">${p.gates.map((g,i)=>`G${i} ${g==='pass'?'✓':g==='fail'?'✗':g==='run'?'⋯':'·'}`).join(' ')}</td></tr>`;const tasks=p.tasks.map(t=>`<tr class="task ${t.status==='running'?'active':''}"><td>T${esc(t.number)}</td><td>↳ ${esc(t.title)}</td><td>${status(t.status)}</td><td>–</td><td>–</td></tr>`);return[phase,...tasks]}).join('');
  $('#updated').textContent=`Atualizado ${new Date(state.updated_at*1000).toLocaleTimeString()}`;
  const canStop = m.status === 'running' || m.status === 'waiting';
  const stopBtn = $('#stop-run');
  if (stopBtn && !stopBtn.dataset.busy) {
    stopBtn.style.display = canStop ? 'inline-block' : 'none';
  }
}

function duration(start,end){if(!start)return'—';let s=Math.max(0,(Number(end)||Math.floor(Date.now()/1000))-Number(start));const h=Math.floor(s/3600),m=Math.floor(s%3600/60);return h?`${h}h ${m}m`:`${m}m ${s%60}s`}
function nearLogEnd(){const logs=$('#logs');return logs.scrollHeight-logs.scrollTop-logs.clientHeight<40}
function scrollLogsToEnd(){const logs=$('#logs');requestAnimationFrame(()=>{logs.scrollTop=logs.scrollHeight})}
function setFollowLogs(value){followLogs=value;const button=$('#follow-logs');button.classList.toggle('active',value);button.setAttribute('aria-pressed',String(value));button.textContent=value?'Seguindo':'Seguir logs';$('#log-status').textContent=value?'Seguindo novas linhas':'Rolagem pausada para leitura';if(value)scrollLogsToEnd()}
function renderLogs(text,replace){const logs=$('#logs');if(replace){logs.textContent=text||'Aguardando logs…';logs.dataset.placeholder=text?'false':'true'}else if(text){if(logs.dataset.placeholder==='true')logs.textContent='';logs.textContent+=text;logs.dataset.placeholder='false'}if(followLogs)scrollLogsToEnd()}
async function refreshRuns(){const data=await fetch('/api/v1/runs',{cache:'no-store'}).then(r=>r.json());const select=$('#runs'), previous=selected;select.replaceChildren(...data.runs.map(run=>{const opt=document.createElement('option');opt.value=run.current?'current':run.id;opt.textContent=`${run.current?'● ':''}${run.id||'legado'} · ${run.status||'sem estado'}`;return opt}));if([...select.options].some(o=>o.value===previous))select.value=previous;else {selected=select.value||'current'};}
async function refresh(){try{await refreshRuns();const url=selected==='current'?'/api/v1/runs/current':`/api/v1/runs/${encodeURIComponent(selected)}`;const state=await fetch(url,{cache:'no-store'}).then(r=>r.json());render(state);const runId=state.run?.id;if(runId){const after=logOffsets.get(runId)||0;const logs=await fetch(`/api/v1/runs/${encodeURIComponent(runId)}/logs?after=${after}`,{cache:'no-store'}).then(r=>r.json());renderLogs(logs.text,logs.truncated||after===0);logOffsets.set(runId,logs.next_offset);}}catch(error){$('#notice').textContent=`Falha ao ler o estado: ${error.message}`}}

$('#runs').addEventListener('change',e=>{selected=e.target.value;$('#logs').textContent='Aguardando logs…';$('#logs').dataset.placeholder='true';setFollowLogs(true);refresh()});
$('#logs').addEventListener('scroll',()=>{if(followLogs&&!nearLogEnd())setFollowLogs(false);else if(!followLogs&&nearLogEnd())setFollowLogs(true)});
$('#follow-logs').addEventListener('click',()=>setFollowLogs(!followLogs));
$('#jump-logs').addEventListener('click',()=>setFollowLogs(true));
$('#input').addEventListener('change',e=>loadPhasesForInput(e.target.value));
$('#refresh-models').addEventListener('click',()=>loadModels(true));
$('#add-model').addEventListener('click',()=>{
  const route=$('#model-picker').value;
  if(!route)return;
  if(!priorityQueue.includes(route)){
    priorityQueue.push(route);
    renderPriorityQueue();
  }
});
$('#phases-pending').addEventListener('click',()=>{
  selectedPhases=new Set(loadedPhases.filter(p=>!p.done).map(p=>p.number));
  renderPhasesChecklist();
});
$('#phases-all').addEventListener('click',()=>{
  selectedPhases=new Set(loadedPhases.map(p=>p.number));
  renderPhasesChecklist();
});
$('#phases-none').addEventListener('click',()=>{
  selectedPhases.clear();
  renderPhasesChecklist();
});

$('#stop-run')?.addEventListener('click',async()=>{
  if(!confirm('Deseja realmente encerrar a execução do Ralph?'))return;
  const btn=$('#stop-run');
  btn.dataset.busy='true';
  btn.disabled=true;
  btn.textContent='Encerrando…';
  try{
    const target=selected==='current'?'current':encodeURIComponent(selected);
    const res=await fetch(`/api/v1/runs/${target}/stop`,{method:'POST',headers:{'Content-Type':'application/json'}});
    const data=await res.json();
    if(!res.ok){throw new Error(data.message||data.error||'Erro ao encerrar')}
    $('#notice').textContent=data.message||'Execução encerrada.';
    delete btn.dataset.busy;
    btn.textContent='Encerrar Ralph';
    await refresh();
  }catch(err){
    $('#notice').textContent=`Falha ao encerrar: ${err.message}`;
    delete btn.dataset.busy;
    btn.disabled=false;
    btn.textContent='Encerrar Ralph';
  }
});

$('#save-config').addEventListener('click',async()=>{
  try{
    const data=await postJson('/api/v1/config',currentConfig());
    $('#notice').textContent=data.message;
  }catch(error){
    $('#notice').textContent=error.message;
  }
});

$('#start-run').addEventListener('click',async()=>{
  try{
    const input=$('#input').value;
    if(!input)throw new Error('Selecione um documento PHASES.md / Feature');
    const phases=[...selectedPhases].sort((a,b)=>a-b);
    if(!phases.length)throw new Error('Selecione ao menos uma fase para implementar');
    if(!priorityQueue.length)throw new Error('Adicione ao menos um modelo na fila de prioridade');
    const cfg=currentConfig();
    await postJson('/api/v1/config',cfg);
    const data=await postJson('/api/v1/runs',{
      input,
      phases,
      model_queue:cfg.models.priority_queue,
      verify_queue:cfg.models.verify_queue
    });
    $('#notice').textContent=data.message;
    setTimeout(refresh,500);
  }catch(error){
    $('#notice').textContent=error.message;
  }
});

$('#logs').dataset.placeholder='true';
loadControls();
refresh();
setInterval(refresh,1000);
