'use strict';
const G=window.Cycloid,$=id=>document.getElementById(id);
const S=window.CycloidStudies,storageKey='cycloidal-v5-design-library-v1';
let motionResult=null,motionStored=false,scanToken=0,scanning=false,designs=[];
let state={...G.defaults},model,playing=false,phase=0,lastTime=0;
const fields=[
 ['ratio','Reduction / N contacts',3,60,1,'N:1 casing output; disc has N−1 lobes'],
 ['radiusBuffer','Extra radius buffer',0,25,.05,'mm · added above the calculated minimum radius'],
 ['roller','Lobe / contact radius',.3,10,.05,'mm · radius of each circular ring contact'],
 ['eccentricity','Eccentricity',.1,5,.05,'mm · orbit radius of the disc centre'],
 ['radius','Contact pitch radius',10,150,.05,'mm · centre to ring-contact centre'],
 ['clearance','Profile clearance',0,1,.05,'mm · radial offset added to contact radius'],
 ['wall','Outer casing wall',.8,6,.1,'mm · internal feature webs stay at 2 mm'],
 ['thickness','Disc thickness',2,12,.1,'mm · each of the two opposed discs'],
 ['gap','Gap between discs',.1,3,.1,'mm · axial gap, not radial clearance'],
 ['postRadius','Standoff body radius',1.7,12,.05,'mm · each of the three standoffs'],
 ['postPitch','Standoff position radius',3,70,.05,'mm · gearbox centre to standoff centre'],
 ['guideRadius','Static screw radius',.5,6,.05,'mm · guide shank radius; M3 starts at 1.50'],
 ['guidePitch','Static screw position radius',3,70,.05,'mm · gearbox centre to guide screw centre']
];
$('fields').innerHTML=fields.map(([key,label,min,max,step,note])=>`<div class="field"><div class="field-head"><label for="${key}">${label}</label><input id="${key}" type="number" min="${min}" max="${max}" step="${step}" aria-describedby="${key}-note"></div><input id="${key}-range" type="range" min="${min}" max="${max}" step="${step}" aria-label="${label} slider"><small id="${key}-note">${note}</small></div>`).join('');
$('preset').innerHTML=G.presets.map((p,i)=>`<option value="${i}">${p.name}</option>`).join('')+'<option value="custom">Custom geometry</option>';
const bearingKeys=['referenceBearing','topBearing','bottomBearing'];
for(const key of bearingKeys){
 $(key).innerHTML=(key==='referenceBearing'?'':'<option value="none">None / no centre seat</option>')+['6700','6800'].map(series=>`<optgroup label="${series} series">${Object.values(G.bearings).filter(b=>b.series===series).map(b=>`<option value="${b.id}">${b.name} · ${b.bore} × ${b.od} × ${b.width} mm</option>`).join('')}</optgroup>`).join('');
 $(key).onchange=()=>{state[key]=$(key).value;edit();};
}
function sync(){for(const [k] of fields){$(k).value=state[k];$(`${k}-range`).value=state[k];}for(const k of bearingKeys)$(k).value=state[k]; $('auto').checked=state.auto;$('radius').disabled=$('radius-range').disabled=state.auto;$('radiusBuffer').disabled=$('radiusBuffer-range').disabled=!state.auto;}
function setPreset(i){stop();state={...G.presets[i].values};phase=0;$('phase').value=0;$('preset').value=i;$('preset-note').textContent=G.presets[i].note;sync();render();}
function edit(){ $('preset').value='custom';$('preset-note').textContent='Custom geometry · compare the checks below before exporting.';render();}
for(const [key] of fields){for(const suffix of ['', '-range']){$(key+suffix).addEventListener('input',event=>{state[key]=event.target.value===''?NaN:Number(event.target.value);$(key+(suffix?'':'-range')).value=event.target.value;edit();});}}
$('preset').addEventListener('change',()=>{if($('preset').value!=='custom')setPreset(Number($('preset').value));});
$('reset').onclick=()=>setPreset(0);
$('auto').onchange=()=>{state.auto=$('auto').checked;sync();edit();};
function f(v,d=2){return Number.isFinite(v)?v.toFixed(d):'—';}
function margin(){const v=Number($('clearance-margin').value);return Number.isFinite(v)&&v>=0&&v<=5?v:.1;}
function draw(){if(!model)return;const result=window.CycloidDiagram.render(model,phase,{underlay:$('underlay').checked,margin:margin()});$('drawing').innerHTML=result.svg;$('phase-value').textContent=`${f(phase,0)}°`;
 const count=result.overlaps.flat().length;
 $('overlap-status').textContent=count?`${count} planar overlaps at this input angle`:'No planar overlaps at this input angle';
 $('overlap-status').className='badge'+(count?' pink-badge':'');
 $('overlap-list').textContent=result.overlaps.flatMap((arr,i)=>arr.map(o=>`${i?'Bottom':'Top'}: ${o.label}`)).slice(0,12).join(' · ')+(count>12?` · ${count-12} more`:'');
}
function render(){
 invalidateMotion();
 try {model=G.calculate(state);} catch(error){stop();model=null;$('drawing').innerHTML='';const el=document.createElement('p');el.className='error';el.textContent=error.message;$('drawing').append(el);$('health').textContent='Invalid input';$('health').className='badge bad';$('checks').innerHTML='';$('dimensions').innerHTML='';$('metrics').innerHTML='';$('radius-summary').textContent=error.message;$('overlap-status').textContent='Enter valid geometry to inspect overlaps';$('overlap-list').textContent='';for(const id of ['save-config','save-svg','print','share','play'])$(id).disabled=true;return;}
 state.radius=model.p.radius;sync();$('phase').max=360*state.ratio;phase%=360*state.ratio;$('phase').value=phase;
 $('save-design').disabled=false;$('check-motion').disabled=!model.profileValid;
 const minimumText=model.minimumRadius===null?'No minimum within the 150 mm range':`Minimum ${f(model.minimumRadius)} mm`;
 $('radius-summary').innerHTML=`<strong>${state.auto?`${minimumText} + ${f(model.appliedBuffer)} mm buffer = ${f(state.radius)} mm`:`Manual radius ${f(state.radius)} mm · ${minimumText.toLowerCase()}`}</strong><span>Minimum under V5 rules, in 0.05 mm steps. Limited by: ${model.limitingFeature}.</span>`+
   (state.auto&&Math.abs(model.appliedBuffer-state.radiusBuffer)>.000001?`<span>Requested buffer ${f(state.radiusBuffer,3)} mm; rounded upward with the pitch radius.</span>`:'')+
   (!model.valid?'<span class="sizing-warning">Other fit checks need attention. A larger radius cannot resolve every clash.</span>':'');
 for(const id of ['save-config','print','share','play'])$(id).disabled=false;
 $('save-svg').disabled=!model.profileValid;
 $('diagram-title').textContent=`${model.n} contacts / ${model.lobes} lobes`;
 $('health').className='badge'+(model.valid?'':' bad');$('health').textContent=model.valid?'Screening checks pass':`${model.checks.filter(c=>!c.ok).length} checks need attention`;
 $('metrics').innerHTML=[[`${model.n}:1`,'Casing reduction'],[f(model.casingRadius*2,1),'Casing diameter · mm'],[f(model.tipRadius*2,2),'Disc tip diameter · mm'],[f(model.p.radius,2),'Pitch radius · mm']].map(([v,l])=>`<div class="metric"><strong>${v}</strong><span>${l}</span></div>`).join('');
 $('checks').innerHTML=model.checks.map(c=>`<div class="check ${c.ok?'':'bad'}"><span>${c.ok?'✓':'!'}</span><b>${c.name}</b><span>${c.value}</span><small>${c.explanation}</small></div>`).join('');
 const bearingRow=i=>{const b=model.centreBearings[i];return b?`${b.name}: ${b.bore} × ${b.od} × ${b.width} / Ø${f(model.seats[i]*2)}`:'None (no seat)';};
 const rows=[['Ring contacts / disc lobes',`${model.n} / ${model.lobes}`],['Minimum pitch radius (V5 rules)',f(model.minimumRadius)],['Requested / applied radius buffer',state.auto?`${f(state.radiusBuffer)} / ${f(model.appliedBuffer)}`:`${f(state.radiusBuffer)} / not applied (manual)`],['Selected pitch radius',f(state.radius)],['Maximum pitch radius through V5 lip',f(model.maximumLipRadius)],['Contact diameter',`Ø${f(2*state.roller)}`],['Profile clearance',f(state.clearance)],['Disc root / tip diameter',`Ø${f(2*model.rootRadius)} / Ø${f(2*model.tipRadius)}`],['Swept disc envelope',`Ø${f(2*model.sweptRadius)}`],['Static screw diameter / position radius',`Ø${f(2*state.guideRadius)} / ${f(state.guidePitch)}`],['6 guide holes / pitch circle',`Ø${f(2*model.guideHole)} / Ø${f(2*state.guidePitch)}`],['Standoff diameter / position radius',`Ø${f(2*state.postRadius)} / ${f(state.postPitch)}`],['3 standoff holes / pitch circle',`Ø${f(2*model.postHole)} / Ø${f(2*state.postPitch)}`],['Top centre bearing / seat',bearingRow(0)],['Bottom centre bearing / seat',bearingRow(1)],['Reference bearing (scale only)',`${model.reference.name}: ${model.reference.bore} × ${model.reference.od} × ${model.reference.width}`],['Retained casing bearing / seat','6810: 50 × 65 × 7 / Ø65.20'],['Disc thickness / axial gap',`${f(state.thickness)} / ${f(state.gap)}`],['2 casing bearings + 2 discs + gap',`${f(model.bearingStack)} (not overall height)`],['Undercut offset limit',f(model.rho,3)]];
 $('dimensions').innerHTML='<table><tbody>'+rows.map(([a,b])=>`<tr><th scope="row">${a}</th><td>${b}</td></tr>`).join('')+'</tbody></table>';draw();
 if(!model.profileValid)stop();
 $('play').disabled=!model.profileValid;
}
function stop(){playing=false;$('play').textContent='▶ Animate';$('play').setAttribute('aria-pressed','false');}
$('play').onclick=()=>{if(playing){stop();return;}playing=true;lastTime=0;$('play').textContent='Ⅱ Pause';$('play').setAttribute('aria-pressed','true');requestAnimationFrame(tick);};
function tick(t){if(!playing)return;if(!lastTime||t-lastTime>=50){if(lastTime)phase=(phase+Math.min(t-lastTime,100)*.055)%(360*state.ratio);lastTime=t;$('phase').value=phase;draw();}requestAnimationFrame(tick);}
$('phase').oninput=()=>{stop();phase=Number($('phase').value);draw();};$('underlay').onchange=draw;
function download(text,name,type){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('save-config').onclick=()=>download(JSON.stringify({version:'version_6',description:'Shared gearbox controls; run Check / Update before manufacture',explorer:{...model.p},input_angle:phase,reference_underlay:$('underlay').checked?1:0,amber_clearance:margin()},null,2),'gearbox-controls.json','application/json');
$('save-svg').onclick=()=>download(window.CycloidDiagram.render(model,phase,{underlay:$('underlay').checked,margin:margin()}).svg,'cycloidal-diagram.svg','image/svg+xml');
$('print').onclick=()=>{stop();window.print();};
$('share').textContent='Copy settings';
$('share').onclick=async()=>{try{await navigator.clipboard.writeText(JSON.stringify(model.p,null,2));$('action-status').textContent='Settings copied as JSON.';}catch{download(JSON.stringify(model.p,null,2),'cycloidal-settings.json','application/json');$('action-status').textContent='Clipboard unavailable; settings downloaded instead.';}};
function invalidateMotion(){
 scanToken++;scanning=false;motionResult=null;motionStored=false;
 $('motion-progress').hidden=true;$('motion-progress').value=0;$('cancel-motion').hidden=true;
 $('jump-worst').disabled=true;$('check-motion').disabled=true;$('save-design').disabled=true;
 $('motion-status').className='';$('motion-status').textContent='Not checked. Run a full-motion check for these settings.';
}
function showMotion(){
 if(!motionResult)return;
 const r=motionResult,kind=r.gap< -1e-6?'Overlap found':r.gap<margin()?'Below clearance margin':'No overlap at sampled positions';
 $('motion-status').className=r.gap< -1e-6?'motion-pink':r.gap<margin()?'motion-amber':'motion-good';
 $('motion-status').textContent=`${motionStored?'Stored result — ':''}${kind}. Minimum ${f(r.gap,3)} mm · ${r.side?'Bottom':'Top'}: ${r.label} · input ${r.angle}°. 360 positions per cycloid, 1° steps.${!model.valid?' Other geometry checks need attention.':''}`;
 $('jump-worst').disabled=false;
}
$('check-motion').onclick=async()=>{
 stop();invalidateMotion();const token=scanToken,checkedModel=model;scanning=true;
 $('cancel-motion').hidden=false;$('motion-progress').hidden=false;$('save-design').disabled=true;
 $('motion-status').textContent='Checking both cycloids… 0 / 360 input positions.';
 try{
   const r=await S.scan(checkedModel,{cancelled:()=>token!==scanToken,onProgress:(n,total)=>{
     if(token!==scanToken)return;$('motion-progress').value=n;$('motion-status').textContent=`Checking both cycloids… ${n} / ${total} input positions.`;
   }});
   if(token!==scanToken||!r)return;
   motionResult=r;motionStored=false;showMotion();
 }catch(error){if(token===scanToken)$('motion-status').textContent=error.message;}
 finally{if(token===scanToken){scanning=false;$('cancel-motion').hidden=true;$('motion-progress').hidden=true;$('check-motion').disabled=!model?.profileValid;$('save-design').disabled=!model;}}
};
$('cancel-motion').onclick=()=>{invalidateMotion();$('check-motion').disabled=!model?.profileValid;$('save-design').disabled=!model;$('motion-status').textContent='Check cancelled. No complete motion result is available.';};
$('jump-worst').onclick=()=>{if(!motionResult)return;stop();phase=motionResult.angle;$('phase').value=phase;draw();$('drawing').scrollIntoView({block:'nearest',behavior:'smooth'});};
$('clearance-margin').oninput=()=>{if($('clearance-margin').value===''||!$('clearance-margin').checkValidity())return;showMotion();draw();};
function envelope(){return {format:'cycloidal-design-library',version:S.VERSION,designs};}
function persist(message){
 try{localStorage.setItem(storageKey,JSON.stringify(envelope()));$('library-status').textContent=message+' Saved in this browser.';}
 catch{$('library-status').textContent=message+' Browser storage is unavailable or full; export the library to keep these designs.';}
 renderLibrary();
}
const summaryCache=new WeakMap();
function renderLibrary(){
 $('export-library').disabled=!designs.length;
 const host=$('comparison');host.replaceChildren();
 if(!designs.length){host.textContent='No saved designs yet. Name the current design and save it to start comparing.';return;}
 const table=document.createElement('table');table.innerHTML='<caption>Saved designs — nominal millimetres; sampled clearance can be negative.</caption><thead><tr><th scope="col">Name</th><th scope="col">Ratio</th><th scope="col">Casing Ø</th><th scope="col">Disc thickness</th><th scope="col">Bearing / disc stack*</th><th scope="col">Top / bottom bearing</th><th scope="col">Minimum sampled gap</th><th scope="col">Screening</th><th scope="col">Actions</th></tr></thead>';
 const body=document.createElement('tbody');
 designs.forEach((d,i)=>{
   if(!summaryCache.has(d))summaryCache.set(d,G.calculate(d.settings));const m=summaryCache.get(d),tr=document.createElement('tr');
   const cell=text=>{const td=document.createElement('td');td.textContent=text;tr.append(td);return td;};
   const name=cell(''),input=document.createElement('input');input.type='text';input.maxLength=80;input.value=d.name;input.setAttribute('aria-label',`Rename saved design ${i+1}`);name.append(input);
   const rename=()=>{if(!input.value.trim()){input.value=d.name;$('library-status').textContent='A saved design needs a name.';return;}d.name=input.value.trim();persist('Design renamed.');};
   input.onkeydown=event=>{if(event.key==='Enter')rename();};
   cell(`${m.n}:1`);cell(f(2*m.casingRadius));cell(f(m.p.thickness));cell(f(m.bearingStack));cell(`${m.p.topBearing} / ${m.p.bottomBearing}`);
   cell(d.motion?`${f(d.motion.gap,3)} · stored at ${d.motion.angle}°`:'Not checked');
   cell(m.valid?'Pass':`${m.checks.filter(c=>!c.ok).length} need attention`);
   const actions=cell('');
   for(const [title,handler] of [['Rename',rename],['Load',()=>{
     stop();state={...d.settings};phase=0;$('phase').value=0;sync();edit();
     motionResult=d.motion?{...d.motion}:null;motionStored=!!motionResult;showMotion();$('design-name').value=d.name;
     $('library-status').textContent=`Loaded “${d.name}”. Saving again creates a separate snapshot.`;
   }],['Remove',()=>{designs.splice(i,1);persist('Design removed.');}]]){
     const button=document.createElement('button');button.textContent=title;button.setAttribute('aria-label',`${title} ${d.name}`);button.onclick=handler;actions.append(button);
   }
   body.append(tr);
 });table.append(body);host.append(table);
 const note=document.createElement('p');note.className='small';note.textContent='* Two retained 6810 casing bearings + two discs + gap; not overall gearbox height. Stored motion results describe the saved settings; recheck after importing if provenance is uncertain.';host.append(note);
}
$('save-design').onclick=()=>{
 if(!model||scanning)return;
 const name=$('design-name').value.trim();
 if(!name){$('library-status').textContent='Enter a design name first.';$('design-name').focus();return;}
 if(designs.length>=50){$('library-status').textContent='Library is full (50 designs). Export a backup or remove a design first.';return;}
 designs.push({name,settings:{...model.p},motion:motionResult?{...motionResult}:null});persist(`Saved “${name}” as a new snapshot.`);
};
$('export-library').onclick=()=>download(JSON.stringify(envelope(),null,2),'cycloidal-design-library.json','application/json');
$('import-library').onclick=()=>$('library-file').click();
$('library-file').onchange=async()=>{
 const file=$('library-file').files[0];if(!file)return;
 try{
   if(file.size>1000000)throw Error('Library file must be smaller than 1 MB.');
   const incoming=S.library(JSON.parse(await file.text()));
   if(incoming.length+designs.length>50)throw Error('Import would exceed 50 designs; remove some saved designs first.');
   designs.push(...incoming);persist(`Imported ${incoming.length} design${incoming.length===1?'':'s'}.`);
 }catch(error){$('library-status').textContent='Import failed: '+error.message;}
 finally{$('library-file').value='';}
};
try{const saved=localStorage.getItem(storageKey);if(saved)designs=S.library(JSON.parse(saved));$('library-status').textContent=designs.length?`Restored ${designs.length} saved designs.`:'Your saved designs will appear here.';}
catch{$('library-status').textContent='Saved storage is unavailable or unreadable. You can use this session and export a JSON backup.';}
renderLibrary();
let restored=false;
if(location.hash.startsWith('#design=')){try{const candidate=JSON.parse(decodeURIComponent(location.hash.slice(8)));const allowed=Object.fromEntries(Object.keys(G.defaults).filter(k=>k in candidate).map(k=>[k,candidate[k]]));if(typeof allowed.auto!=='boolean')throw Error('Invalid automatic sizing setting');G.calculate(allowed);state={...G.defaults,...allowed};restored=true;}catch{$('action-status').textContent='The design link was invalid; loaded the current V5.';}}
if(restored){sync();edit();}else setPreset(0);
window.addEventListener('beforeprint',stop);
