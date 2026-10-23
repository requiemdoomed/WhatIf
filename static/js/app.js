'use strict';
const main = document.querySelector('main');
let data, csrf, busy = false, viewSequence = 0, toastTimer;
let settings = window.whatifSettings;
const soundtrack = window.WhatIfAudio;
let libraryPage = 1;
let libraryFilters = {query:'',category:'',sort:'featured',progress:'all'};
settings.favourites = Array.isArray(settings.favourites) ? settings.favourites : [];
const svgNS = 'http://www.w3.org/2000/svg';

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'class') node.className = value;
    else if (value !== undefined && value !== false) node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}
function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(svgNS, tag);
  for (const [k,v] of Object.entries(attrs)) node.setAttribute(k,v);
  node.append(...children); return node;
}
const p = (text, cls) => el('p', {class: cls || ''}, text);
const link = (text, hash, cls = 'text-link') => el('a', {href: hash, class: cls}, text);
const button = (text, action, cls = '') => el('button', {class: cls, onclick: () => actionGuard(action)}, text);
function notify(message) {
  const toast = document.querySelector('#toast');
  toast.textContent = message; toast.classList.add('visible');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('visible'), 5000);
}
async function api(path, body) {
  const response = await fetch('/api/' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf || ''},
    ...(body !== undefined ? {body: JSON.stringify(body)} : {})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
  return result;
}
async function actionGuard(action) {
  if (busy) return;
  busy = true; main.setAttribute('aria-busy', 'true');
  try { await action(); }
  catch (error) { notify(error.message || 'Connection interrupted. Your last saved decision is safe.'); }
  finally { busy = false; main.removeAttribute('aria-busy'); }
}
async function refresh() { data = await api('bootstrap'); csrf = data.csrf; }
function go(hash) { if (location.hash === hash) render(); else location.hash = hash; }
function pageTitle(kicker, title, description) {
  return el('div', {}, p(kicker, 'eyebrow'), el('h1', {class: 'page-title'}, title), p(description));
}
function empty(title, description) {
  return el('section', {class:'empty'}, el('h2',{},title),p(description),link('Explore scenarios →','#explore','primary'));
}
function saveSettings() {
  try { localStorage.setItem('whatif-settings', JSON.stringify(settings)); }
  catch (_) { notify('This browser cannot save preferences. They will last for this tab only.'); }
  document.documentElement.dataset.theme = settings.theme === 'system' || !settings.theme ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : settings.theme;
  document.documentElement.dataset.motion = settings.motion || 'system';
  document.documentElement.dataset.readability = settings.readability || 'normal';
  document.querySelector('#theme').setAttribute('aria-label', `Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme`);
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (!settings.theme || settings.theme === 'system') saveSettings(); });
document.querySelector('#theme').addEventListener('click', () => {
  settings.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; saveSettings();
  if (location.hash === '#settings') render();
});
function playSound(ending = false) {
  if (settings.sound) soundtrack.chime(ending);
}
async function enableSound() {
  await soundtrack.enable(); settings.music = true; saveSettings();
}
let awaitingSoundGesture = true;
const audioToggle = document.querySelector('#audio-toggle');
audioToggle.addEventListener('click', () => {
  if (soundtrack.status().enabled) { soundtrack.pause(); settings.music = false; saveSettings(); }
  else enableSound().catch(error => notify(error.message));
});
const volumeControl = document.querySelector('#audio-volume');
volumeControl.value = String(Math.round((Number.isFinite(settings.volume) ? settings.volume : .35) * 100));
soundtrack.setVolume(Number(volumeControl.value) / 100);
volumeControl.addEventListener('input', () => {
  settings.volume = Number(volumeControl.value) / 100; soundtrack.setVolume(settings.volume); saveSettings();
});
soundtrack.subscribe(status => {
  const label = status.enabled ? 'Pause soundtrack' : 'Play soundtrack';
  audioToggle.setAttribute('aria-label', label); audioToggle.title = label;
  audioToggle.setAttribute('aria-pressed', String(status.enabled));
  document.querySelector('#audio-status').textContent = status.loading ? 'Loading soundtrack…' : status.enabled ? '♫ ' + status.title : (awaitingSoundGesture ? 'Tap anywhere to begin the music' : 'Sound paused · press ♫ to listen');
});
// The first real interaction unlocks audio; a later pause stays paused.
function unlockSound(event) {
  if (!event.isTrusted || !awaitingSoundGesture) return;
  if (event.type === 'keydown' && (event.repeat || ['Shift','Control','Alt','Meta','Escape'].includes(event.key))) return;
  awaitingSoundGesture = false;
  for (const type of ['click','touchend','keydown']) document.removeEventListener(type, unlockSound, true);
  // Let the dedicated toggle handle its own first click without toggling twice.
  if (event.target instanceof Element && event.target.closest('#audio-toggle')) return;
  enableSound().catch(error => notify(error.message + ' Use ♫ to try again.'));
}
for (const type of ['click','touchend','keydown']) document.addEventListener(type, unlockSound, {capture:true, passive:true});
async function previewSound(story) {
  await soundtrack.scene(story.audio, story.id);
  await enableSound(); notify('Previewing the atmosphere for ' + story.title + '.');
}
function confirmAction(title, description, reset = false) {
  const dialog = document.querySelector('#confirm-dialog');
  document.querySelector('#dialog-title').textContent = title;
  document.querySelector('#dialog-description').textContent = description;
  document.querySelector('#reset-label').hidden = !reset;
  const input = document.querySelector('#reset-word'); input.value = '';
  const confirm = document.querySelector('#confirm-action'); confirm.disabled = reset;
  input.oninput = () => { confirm.disabled = reset && input.value !== 'RESET'; };
  dialog.returnValue = 'cancel'; dialog.showModal();
  return new Promise(resolve => dialog.addEventListener('close', () => resolve(dialog.returnValue === 'ok' && (!reset || input.value === 'RESET')), {once:true}));
}
async function start(id) { const journey = await api('journeys', {scenario:id}); go('#play/' + journey.id); }
async function fork(journey, step) {
  const branch = await api(`journeys/${journey.id}/fork`, {step});
  notify('New branch created. Your original journey is preserved.'); go('#play/' + branch.id);
}
function scenarioCard(story, number) {
  const active = data.journeys.find(j => j.scenario === story.id && !j.completed);
  return el('article', {class:'card'},
    el('div', {class:'cover ' + story.audio, 'aria-hidden':'true'},el('img',{class:'world-art',src:'/static/art/'+story.audio+'.svg',alt:'',loading:'lazy'}),el('span',{class:'number'},`WORLD ${String(number + 1).padStart(3,'0')}`),el('span',{class:'symbol'},story.symbol)),
    el('div', {class:'card-body'},el('span',{class:'badge'},story.category),el('h3',{},story.title),p(story.description),p(`${story.routes} verified routes · ${story.structure}`, 'route-count'),story.content_note ? p(story.content_note,'small content-note') : null,
      el('div',{class:'meta'},el('span',{},`${story.difficulty} · ~${story.minutes} min`),el('span',{},`${story.discovered.length}/${story.endings} endings`)),
      button(active ? 'Continue journey ↗' : 'Enter scenario ↗', () => active ? go('#play/' + active.id) : start(story.id)),
      active ? button('Start a separate journey', () => start(story.id)) : null,
      el('div',{class:'card-tools'},button('♫ Preview atmosphere',()=>previewSound(story),'subtle'),
        bookmarkButton(story))));
}
function bookmarkButton(story) {
  const control=button(settings.favourites.includes(story.id)?'★ Saved':'☆ Save',()=>{
    const saved=settings.favourites.includes(story.id);
    settings.favourites=saved?settings.favourites.filter(id=>id!==story.id):[...settings.favourites,story.id];
    saveSettings();control.textContent=saved?'☆ Save':'★ Saved';
    const progress=document.querySelector('[aria-label="Filter progress"]');
    if(progress?.value==='saved')progress.dispatchEvent(new Event('change'));
  },'subtle');
  return control;
}
function heroArt() {
  return el('div', {class:'hero-art'}, svg('svg',{viewBox:'0 0 440 370',role:'img','aria-label':'One decision branches into three possible futures'},
    svg('ellipse',{cx:220,cy:185,rx:150,ry:150,class:'art-line'}),
    svg('ellipse',{cx:220,cy:185,rx:108,ry:108,class:'art-line'}),
    svg('path',{d:'M65 210 H155 Q190 210 210 170 L285 95 M155 210 H365 M155 210 Q205 210 225 265 L290 310',class:'art-line'}),
    svg('path',{d:'M65 210 H155 Q190 210 210 170 L285 95',class:'art-path'}),
    ...[[65,210],[155,210],[285,95],[365,210],[290,310]].map(([cx,cy]) => svg('circle',{cx,cy,r:7,class:'art-node'})),
    ...[[37,244,'YOU ARE HERE'],[245,68,'THE UNEXPECTED'],[282,243,'THE FAMILIAR'],[242,344,'THE UNKNOWN']].map(([x,y,t])=>svg('text',{x,y,class:'art-text'},document.createTextNode(t))),
    svg('text',{x:154,y:181,class:'art-big'},document.createTextNode('What if?'))));
}
function home() {
  return [el('section',{class:'hero'},el('div',{},p('The anthology · Volume II','eyebrow'),el('h1',{},'One Decision.',el('br'),el('em',{},'Infinite'),el('br'),'Possibilities.'),p('The smallest choice can change the whole story. Step into another reality. Follow your instincts. Then discover what might have been.'),el('div',{class:'actions'},link('Start Exploring ↗','#explore','primary'),link('Visit the Timeline Lab','#lab'),el('span',{class:'small'},'♫ Music begins with your first touch')),p(`${data.totals.scenarios} worlds · ${data.totals.endings} endings · ${data.totals.routes.toLocaleString()} verified routes`,'small')),heroArt()),
    el('section',{},el('div',{class:'section-head'},el('div',{},p('Choose your first world','eyebrow'),el('h2',{},'Every story starts with you.')),link('View all scenarios →','#explore')),el('div',{class:'cards'},[data.scenarios[0],data.scenarios.find(s=>s.category==='Cyberpunk'),data.scenarios.find(s=>s.category==='Quantum')].filter(Boolean).map(s=>scenarioCard(s,data.scenarios.indexOf(s))))),
    el('section',{class:'how'},[['01','Make a choice','Read the scene, check your resources and decide what matters. Every decision is saved automatically.'],['02','Follow the consequences','Find evidence, build trust and discover the ending your decisions make possible.'],['03','Ask “what if?”','Return to an earlier decision. Create another route and compare it with the original.']].map(([n,t,d])=>el('div',{},el('span',{class:'step-number'},n),el('strong',{},t),p(d))))];
}
function explore() {
  const cards = el('div',{class:'cards'}), count = el('p', {class:'small',role:'status','aria-live':'polite'});
  const pages = el('div',{class:'pagination'});
  const search = el('input',{type:'search',placeholder:'Search 105 worlds, clues and possibilities…','aria-label':'Search scenarios'});
  search.value = libraryFilters.query;
  const category = el('select',{'aria-label':'Filter by category'},el('option',{value:''},'All genres'),
    [...new Set(data.scenarios.map(s=>s.category))].sort().map(c=>el('option',{value:c},c)));
  category.value=libraryFilters.category;
  const sort = el('select',{'aria-label':'Sort scenarios'},el('option',{value:'featured'},'Featured order'),el('option',{value:'title'},'Title A–Z'),el('option',{value:'discovery'},'Least explored'),el('option',{value:'routes'},'Most routes'));
  sort.value=libraryFilters.sort;
  const progress = el('select',{'aria-label':'Filter progress'},[['all','All worlds'],['new','Undiscovered'],['played','Endings discovered'],['saved','Saved for later']].map(([value,label])=>el('option',{value},label)));
  progress.value=libraryFilters.progress;
  function filter(reset = false) {
    if(reset)libraryPage=1;
    libraryFilters={query:search.value,category:category.value,sort:sort.value,progress:progress.value};
    const q = search.value.trim().toLowerCase();
    const matches = data.scenarios.filter(s=>(!category.value || s.category === category.value) &&
      (s.title+' '+s.description+' '+s.tags.join(' ')).toLowerCase().includes(q) &&
      (progress.value!=='new'||!s.discovered.length) && (progress.value!=='played'||s.discovered.length) &&
      (progress.value!=='saved'||settings.favourites.includes(s.id)));
    if(sort.value==='title')matches.sort((a,b)=>a.title.localeCompare(b.title));
    if(sort.value==='discovery')matches.sort((a,b)=>a.discovered.length-b.discovered.length);
    if(sort.value==='routes')matches.sort((a,b)=>b.routes-a.routes);
    const size=12, total=Math.max(1,Math.ceil(matches.length/size));
    libraryPage=Math.min(libraryPage,total);
    const start=(libraryPage-1)*size;
    cards.replaceChildren(...matches.slice(start,start+size).map(s=>scenarioCard(s,data.scenarios.indexOf(s))));
    if(!matches.length)cards.append(p('No worlds match. Try another word, genre or progress filter.'));
    count.textContent=matches.length ? `${matches.length} scenarios · Showing ${start+1}–${Math.min(start+size,matches.length)}` : '0 scenarios';
    const previous=button('← Previous',()=>{libraryPage--;filter();cards.scrollIntoView({block:'start'});}); previous.disabled=libraryPage===1;
    const next=button('Next →',()=>{libraryPage++;filter();cards.scrollIntoView({block:'start'});}); next.disabled=libraryPage>=total;
    pages.replaceChildren(previous,p(`Page ${libraryPage} of ${total}`,'small'),next);
  }
  search.addEventListener('input',()=>filter(true));
  for(const control of [category,sort,progress])control.addEventListener('change',()=>filter(true));
  filter();
  const surprise=button('Choose a world for me ↗',()=>{
    const unplayed=data.scenarios.filter(s=>!s.discovered.length);
    const pool=unplayed.length?unplayed:data.scenarios;
    const random=new Uint32Array(1);crypto.getRandomValues(random);
    return startScenarioFromPool(pool[random[0]%pool.length]);
  });
  return [pageTitle('The scenario library','A hundred ways to begin.',`${data.totals.scenarios} short interactive stories. Three endings each. Every route checked.`),
    el('div',{class:'actions'},surprise,p('Retro evenings. Quantum mornings. Futures worth questioning.','small')),
    el('div',{class:'toolbar library-toolbar'},search,category,sort,progress),count,cards,pages];
}
function startScenarioFromPool(story) { notify('Your next world: '+story.title); return start(story.id); }
function historyList(journey, branching = true) {
  const list = el('ol',{class:'route'});
  journey.snapshot.history.forEach((h,i)=>list.append(el('li',{},el('strong',{},`${i+1}. ${h.label}`),p(h.consequence),p(Object.entries(h.after).map(([k,v])=>`${k}: ${h.before[k]} → ${v}`).join(' · '),'small'),branching ? button('Branch before this decision ↗',()=>fork(journey,i)) : null)));
  list.append(el('li',{class:'current'},el('strong',{},journey.completed ? 'Ending reached' : 'Current decision point'),p(journey.node ? journey.node.title : `${journey.snapshot.history.length} decisions recorded`)));
  return list;
}
function statePanel(journey) {
  const maxima = {time:6,resources:3,trust:3};
  return el('aside',{class:'panel sidebar'},p('Your current reality','eyebrow'),el('h3',{},'What you carry'),
    Object.entries(journey.snapshot.state).map(([key,value])=>el('div',{class:'state-item'},el('label',{},key[0].toUpperCase()+key.slice(1),el('span',{},`${value}/${maxima[key]}`)),el('progress',{value,max:maxima[key],'aria-label':key}))),
    p('Time = usable intervals; countdown stories need two for a coordinated ending. Resources = available support. Trust = cooperation.','small'),
    el('h3',{},'Evidence'),journey.snapshot.evidence.length ? journey.snapshot.evidence.map(e=>p('◇ '+e,'evidence')) : p('Nothing discovered yet.','small'),
    el('div',{class:'actions'},button('Save a checkpoint',async()=>{await api(`journeys/${journey.id}/checkpoint`,{});notify('Checkpoint saved. Restore it from My Journeys.');}),button('Show a hint',async()=>{const r=await api(`journeys/${journey.id}/hint`,{});const target=document.querySelector('#hint');target.hidden=false;target.textContent=r.hint;}),button('Open Timeline Lab ↗',()=>go('#lab/'+journey.id)),button('Start again',async()=>{if(await confirmAction('Start a new journey?','Your existing journey will remain saved. A new journey begins at the opening scene.'))await start(journey.scenario);})),
    p('Every decision saves automatically.','small'));
}
const atmosphereLabels = {orbital:'Orbital light · distant machinery',tape:'Warm tape · analogue echoes',noir:'Rain on glass · muted midnight',mystery:'Quiet corridors · unanswered questions',neon:'Electric skyline · rain and pulse',city:'Evening windows · a city in motion',quantum:'Interference · drifting harmonics',clock:'Brass and shadow · measured seconds',wilderness:'Open air · wind through the trees',uncanny:'Empty rooms · uneasy resonance'};
function atmosphereBanner(j) {
  const number = [...j.scenario].reduce((v,c)=>(v*31+c.charCodeAt(0))>>>0,7);
  return el('section',{class:'atmosphere-banner','aria-label':'Scenario atmosphere'},
    el('img',{src:'/static/art/'+j.audio+'.svg',alt:''}),
    el('div',{class:'atmosphere-caption'},p('WORLD FREQUENCY · '+String(number%10000).padStart(4,'0'),'eyebrow'),
      el('strong',{},atmosphereLabels[j.audio]),p(j.completed?'The decision is yours. The echoes remain.':'Take a breath. Read closely. Every choice leaves a trace.')));
}
async function player(id) {
  const j = await api('journeys/'+id);
  const choices = el('div',{class:'choices'});
  j.node.choices.forEach((c,i)=> {
    const requirement = Object.entries(c.requires).map(([k,v])=>k==='evidence'?v:`${k} ≥ ${v}`).join(', ');
    const b = button('',async()=>{
      const currentSequence = viewSequence;
      const updated = await api(`journeys/${j.id}/choose`,{version:j.version,scene:j.snapshot.scene,choice:c.id});
      playSound(updated.completed);
      if (currentSequence === viewSequence) await render();
      else notify('Decision saved to your journey.');
      if (updated.completed) notify('Ending discovered. Visit the Timeline Lab to try another route.');
    },'choice');
    b.replaceChildren(el('span',{class:'choice-index'},String(i+1).padStart(2,'0')),el('span',{},c.label,requirement?el('small',{},`${c.available?'Requires':'Locked · requires'} ${requirement}`):null));
    b.disabled = !c.available; choices.append(b);
  });
  let original;
  if (j.parent) { const parent=await api('journeys/'+j.parent); original=parent.snapshot.history[j.fork_index]; }
  return [atmosphereBanner(j),el('div',{class:'section-head'},el('div',{},p(j.parent?'Alternate journey':'Your journey','eyebrow'),el('h1',{class:'page-title'},j.title)),link('Exit · progress saved','#journeys')),
    j.parent && j.snapshot.history.length===j.fork_index ? p(original ? `Original decision: “${original.label}”. Choose another option below to explore a different route.` : 'This branch begins at the original journey’s current position.','consequence') : null,
    el('div',{class:'player'},el('article',{class:'panel story-panel'},p(j.completed?'Reality discovered':`Chapter ${j.snapshot.history.length+1} · ${j.snapshot.history.length} decisions made`,'eyebrow'),el('h2',{},j.node.title),p(j.node.text,'narrative'),
      j.snapshot.history.length ? p(j.snapshot.history.at(-1).consequence,'consequence'):null,
      j.completed ? el('div',{class:'actions'},link('Explore another possibility ↗','#lab/'+j.id,'primary'),j.parent?link('Compare with original','#compare/'+j.parent+'/'+j.id):null) : choices,
      el('p',{id:'hint',class:'hint',hidden:true}),el('details',{},el('summary',{},'Decision journal'),historyList(j,false))),statePanel(j))];
}
function journeyRow(j) {
  const details=el('details',{},el('summary',{},'Route & saved checkpoints'));
  let loaded=false;
  details.addEventListener('toggle',async()=>{
    if(!details.open || loaded)return;
    loaded=true; const body=el('div',{},p('Loading saved route…','small')); details.append(body);
    try {
      const full=await api('journeys/'+j.id);
      body.replaceChildren(historyList(full,false),...(full.checkpoints.length ? full.checkpoints.map(c=>el('div',{class:'actions'},p(`Checkpoint after decision ${c.step}`,'small'),button('Restore as new branch',()=>fork(full,c.step)))) : [p('No manual checkpoints. Your latest position is already saved.','small')]));
    } catch(error) {body.replaceChildren(p(error.message),button('Retry',()=>{body.remove();loaded=false;details.open=false;details.open=true;}));}
  });
  return el('article',{class:'panel journey-row'},el('div',{},el('span',{class:'badge'},j.completed?'Completed':'In progress'),j.parent?el('span',{class:'tag'},'Alternate route'):null,
    el('h3',{},j.title),p(`${j.decision_count} decisions · Last played ${new Date(j.updated).toLocaleString()}`),details),
    el('div',{class:'actions'},link(j.completed?'Review ending':'Resume ↗','#play/'+j.id,'primary'),link('Timeline','#lab/'+j.id),button('Replay',()=>start(j.scenario))));
}
function journeys() {
  const list=el('div'), more=button('Load more journeys',()=>show());let shown=0;
  function show(){const next=data.journeys.slice(shown,shown+15);shown+=next.length;list.append(...next.map(journeyRow));more.hidden=shown>=data.journeys.length;}
  show();const discovered=data.scenarios.filter(s=>s.discovered.length);
  return [pageTitle('Your collection','My Journeys','Your latest position saves automatically. Open a route to inspect its decisions and checkpoints.'),
    data.journeys.length?list:empty('Your first journey is waiting.','Pick a world and make your first decision. We will keep your place here.'),more,
    el('div',{class:'section-head'},el('h2',{},'Discovered endings')),
    discovered.length?el('div',{class:'cards'},discovered.map(story=>el('article',{class:'panel'},el('h3',{},story.title),p(`${story.discovered.length} of ${story.endings} discovered`,'small'),story.discovered.map(t=>p(t))))) : p('Complete a story to begin your collection.')];
}
function graph(j, parent) {
  const nodes=j.graph, byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
  const depth={};
  function mark(id,d) { if ((depth[id]??-1)>=d) return;depth[id]=d;for(const t of byId[id].edges)mark(t,d+1); }
  const targets=new Set(nodes.flatMap(n=>n.edges));
  for(const n of nodes)if(!targets.has(n.id))mark(n.id,0);
  const levels={};for(const n of nodes)(levels[depth[n.id]]??=[]).push(n);
  const positions={};for(const [level,group] of Object.entries(levels))group.forEach((n,i)=>positions[n.id]=[92+Number(level)*145,65+i*110]);
  const taken=new Set(j.snapshot.history.map(h=>h.scene+'/'+h.target));
  const parentVisited=new Set(parent ? parent.snapshot.history.map(h=>h.scene).concat(parent.snapshot.scene):[]);
  const locked=new Set(j.node.choices.filter(c=>!c.available).map(c=>c.target));
  const canvas=svg('svg',{viewBox:`0 0 ${Math.max(...Object.values(depth))*145+190} ${Math.max(320,Math.max(...Object.values(levels).map(group=>group.length))*110+70)}`,class:'graph',role:'img','aria-label':'Story route graph. A complete text route appears below.'});
  for(const n of nodes)for(const target of n.edges){const [x,y]=positions[n.id],[tx,ty]=positions[target];canvas.append(svg('line',{x1:x+48,y1:y,x2:tx-48,y2:ty,class:taken.has(n.id+'/'+target)?'taken':''}));}
  for(const n of nodes){const [x,y]=positions[n.id];const status=n.visited?'visited':locked.has(n.id)?'locked':parentVisited.has(n.id)?'alternate':'unvisited';
    const group=svg('g',{class:status},svg('title',{},document.createTextNode(n.title+' · '+status)),svg('rect',{x:x-55,y:y-27,width:110,height:54,rx:9}),svg('text',{x,y:y-3,'text-anchor':'middle'},document.createTextNode(n.ending?(n.visited?'Ending reached':'Unexplored ending'):n.id)),svg('text',{x,y:y+14,'text-anchor':'middle'},document.createTextNode(status)));
    canvas.append(group);
  }
  return el('div',{class:'graph-wrap'},canvas);
}
async function lab(id) {
  if (!data.journeys.length) return [pageTitle('The Timeline Lab','A different choice. A different world.','Branch at a decision point without changing your original story.'),empty('First, create a timeline.','The lab maps the choices you have actually made. Start a journey to see yours here.')];
  const j=await api('journeys/'+(id || data.journeys[0].id));
  const parent=j.parent?await api('journeys/'+j.parent):null;
  const selector=el('select',{'aria-label':'Select a journey',onchange:e=>go('#lab/'+e.target.value)},data.journeys.map(x=>el('option',{value:x.id,selected:x.id===j.id},`${x.title} · ${x.id.slice(0,5)}${x.parent?' · alternate':''}`)));
  const relatives=data.journeys.filter(x=>x.scenario===j.scenario && x.id!==j.id);
  const compareSelect=el('select',{'aria-label':'Select comparison journey'},relatives.map(x=>el('option',{value:x.id},`${x.title} · ${x.id.slice(0,5)} · ${x.completed?'completed':'in progress'}`)));
  return [pageTitle('The Timeline Lab','Every choice leaves a trace.','Select an earlier decision to preserve this journey and explore a new branch.'),el('div',{class:'toolbar'},selector,link('Open this journey ↗','#play/'+j.id)),graph(j,parent),p('Violet: visited · Gray: unexplored · Dashed: currently locked · Cyan: visited in the parent route. Unexplored outcomes are not discoveries.','legend'),
    el('section',{class:'panel'},el('h2',{},'Your decision points'),historyList(j),!j.snapshot.history.length?p('Make a decision in the story to create your first branch point.'):null),
    el('section',{class:'panel'},el('h2',{},'Compare realities'),relatives.length?el('div',{class:'toolbar'},compareSelect,button('Compare routes →',()=>go('#compare/'+j.id+'/'+compareSelect.value))):p('Create an alternate route above. It will appear here for comparison.'))];
}
async function compare(a,b) {
  const [left,right]=await Promise.all([api('journeys/'+a),api('journeys/'+b)]);
  if(left.scenario!==right.scenario)throw new Error('Choose two journeys from the same scenario.');
  let common=0;while(common<Math.min(left.snapshot.history.length,right.snapshot.history.length)&&left.snapshot.history[common].choice===right.snapshot.history[common].choice)common++;
  return [pageTitle('Alternate realities','Same beginning. Different possibilities.',`${common} shared decisions before the routes diverge or one remains unexplored.`),
    el('div',{class:'compare'},[left,right].map((j,i)=>el('section',{class:'panel'},p(i?'Reality B':'Reality A','eyebrow'),el('h2',{},j.title),p(j.completed?'Completed ending':'Still being explored','badge'),p(j.node.title),p(j.node.text,'narrative'),p(Object.entries(j.snapshot.state).map(([k,v])=>`${k}: ${v}`).join(' · '),'state-summary'),p(j.snapshot.evidence.length?'Evidence: '+j.snapshot.evidence.join(', '):'No evidence found.','small'),historyList(j,false),link(j.completed?'Review this ending':'Continue this reality ↗','#play/'+j.id,'primary'))))];
}
function achievements() {
  return [pageTitle('Small discoveries. Lasting differences.','Achievements',`${data.achievements.filter(a=>a.earned).length} of ${data.achievements.length} earned from your actual journeys.`),el('div',{class:'cards'},data.achievements.map(a=>el('article',{class:'card achievement '+(a.earned?'':'locked')},el('span',{class:'medal','aria-hidden':'true'},a.earned?'✦':'◇'),el('span',{class:'badge'},a.earned?'Unlocked':'Not yet discovered'),el('h3',{},a.title),p(a.description),a.earned?p(new Date(a.earned).toLocaleDateString(),'small'):null)))];
}
function settingsView() {
  function setting(label,description,key,options) {
    const select=el('select',{id:'setting-'+key,onchange:e=>{settings[key]=key==='sound'?e.target.value==='on':e.target.value;saveSettings();}},options.map(([v,t])=>el('option',{value:v,selected:(key==='sound'?(settings.sound?'on':'off'):(settings[key]||options[0][0]))===v},t)));
    return el('div',{class:'setting'},el('div',{},el('label',{for:'setting-'+key},label),p(description)),select);
  }
  return [pageTitle('Make yourself at home','Settings & About','A quieter screen, a larger story, or a fresh beginning.'),el('section',{class:'panel settings'},
    setting('Appearance','Use your system preference or choose your own.','theme',[['system','System'],['light','Light'],['dark','Dark']]),
    setting('Motion','System reduction is always respected.','motion',[['system','System'],['reduce','Reduce motion']]),
    setting('Story text','Give the narrative more room to breathe.','readability',[['normal','Standard'],['large','Large']]),
    el('div',{class:'setting'},el('div',{},el('strong',{},'Original soundtrack'),p('Use ♫ in the header to play or pause. Volume is available at the bottom of every page.')),button('Replay opening score',()=>previewSound({audio:'main',id:'lobby',title:'the opening'}))),
    setting('Decision sounds','Soft decision and ending cues when the soundtrack is enabled.','sound',[['off','Off'],['on','On']]),
    el('div',{class:'setting'},el('div',{},el('strong',{},'Reset local progress'),p('Deletes journeys, checkpoints, endings and achievements for this browser profile.')),button('Reset progress',async()=>{if(await confirmAction('Delete your progress?','This cannot be undone. Other browser profiles are not affected.',true)){await api('reset',{confirm:'RESET'});notify('Progress reset. A new beginning awaits.');await render();}},'danger'))),
    el('section',{class:'panel settings'},el('h2',{},'WhatIf — The Alternate Reality Engine'),p('Created by Swayam Shakya. An anthology of 105 short fictional scenarios spanning retro, futuristic, murder mystery, quantum, cyberpunk, modern life and other worlds.'),p('The browser displays the story. A Python decision engine checks each choice through Flask. SQLite stores your journeys and the route you actually took. The same choices always produce the same outcome.'),p('This is a local, anonymous experience. A signed browser cookie identifies your progress. Clearing that cookie or using a different browser starts a separate profile. Keep the database folder and cookie to resume after a restart.'),p('Built with HTML, CSS, vanilla JavaScript, Python, Flask, SQLite and Jupyter Notebook. No external services or accounts are needed.','small'))];
}
async function render() {
  const sequence=++viewSequence;
  const [view='home',a,b]=(location.hash.slice(1)||'home').split('/');
  document.querySelectorAll('nav a').forEach(n=>{const active=n.hash==='#'+view || view==='play'&&n.hash==='#journeys'||view==='compare'&&n.hash==='#lab';n.classList.toggle('active',active);if(active)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
  try {
    await refresh();
    let content;
    if(view==='home')content=home();else if(view==='explore')content=explore();else if(view==='play')content=await player(a);else if(view==='journeys')content=journeys();else if(view==='lab')content=await lab(a);else if(view==='compare')content=await compare(a,b);else if(view==='achievements')content=achievements();else if(view==='settings')content=settingsView();else content=[empty('This page does not exist.','Return to the scenario library to continue.')];
    if(sequence!==viewSequence)return;
    main.replaceChildren(...content.flat(Infinity).filter(Boolean));
    const playing=view==='play'?data.journeys.find(j=>j.id===a):null;
    if(playing)document.body.dataset.atmosphere=playing.audio;else delete document.body.dataset.atmosphere;
    const tension=playing&&!playing.completed ? (6-playing.snapshot.state.time)/6 : 0;
    soundtrack.scene(playing?playing.audio:'main',playing?playing.scenario:'lobby',tension).catch(error=>notify(error.message));
    document.title=`${view==='home'?'One Decision. Infinite Possibilities.':view[0].toUpperCase()+view.slice(1)} · WhatIf`;
    main.focus({preventScroll:true});window.scrollTo({top:0});
  } catch(error) {
    if(sequence!==viewSequence)return;
    main.replaceChildren(el('section',{class:'empty'},el('h2',{},'Let’s reconnect.'),p(error.message),button('Try again',render),link('Back to journeys','#journeys')));
  }
}
window.addEventListener('hashchange',render);
saveSettings(); render();
