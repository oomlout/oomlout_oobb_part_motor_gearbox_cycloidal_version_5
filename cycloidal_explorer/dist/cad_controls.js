/* Optional local bridge; the bundled explorer remains usable offline. */
const cadPanel=document.createElement('section');cadPanel.className='cad-controls';
cadPanel.innerHTML='<h2>Version 6 · build this gearbox</h2><p>Check the complete recipe, then update all native parts together. Each successful update becomes a separate revision. Your last accepted gearbox stays available if a new build fails.</p><div class="library-actions"><button id="cad-check">Check gearbox</button><button id="cad-build">Update gearbox</button><button id="cad-load">Load accepted settings</button><button id="cad-native">Load saved SolidCraft controls</button></div><p id="cad-status" role="status">Connecting to local build service…</p><pre id="cad-detail" style="white-space:pre-wrap;max-height:20rem;overflow:auto"></pre>';
document.querySelector('main').prepend(cadPanel);
let cadConnected=false,cadBusy=false,cadTimer=null;
const cadButtons=['cad-check','cad-build','cad-load','cad-native'];
function cadEnable(){for(const id of cadButtons)$(id).disabled=!cadConnected||cadBusy;}
function cadMessage(text,detail=''){$('cad-status').textContent=text;$('cad-detail').textContent=detail;}
async function cadRequest(path,data){
 const response=await fetch(path,data?{method:'POST',headers:{'Content-Type':'application/json','X-Gearbox-Control':'version_6'},body:JSON.stringify(data)}:{cache:'no-store'});
 if(!response.ok){let error;try{error=(await response.json()).error;}catch{error='Local gearbox service unavailable';}throw Error(error);}
 return response.json();
}
function cadValues(){return {explorer:{...state},input_angle:phase,reference_underlay:$('underlay').checked?1:0,amber_clearance:margin()};}
function cadLoad(data){stop();state={...G.defaults,...data.explorer};phase=data.values.input_angle;$('phase').value=phase;$('underlay').checked=!!data.values.reference_underlay;$('clearance-margin').value=data.values.amber_clearance;sync();edit();}
async function cadPoll(){
 try{const data=await cadRequest('/api/status');cadBusy=data.status==='running';cadEnable();
 if(data.status==='idle')return;
 cadMessage(cadBusy?'Building and validating. This can take several minutes.':data.status==='accepted'?'Accepted. All parts and assembly checks passed.':'Build failed. The previous accepted gearbox is still selected.',data.log+'\n\nSelected parts: '+data.part+'\nBuild log: '+data.log_path);
 if(cadBusy)cadTimer=setTimeout(cadPoll,4000);
 }catch(error){cadMessage(error.message);}
}
$('cad-check').onclick=async()=>{cadBusy=true;cadEnable();cadMessage('Checking dimensions and fixed profile sampling…');try{
 const r=await cadRequest('/api/check',cadValues());cadMessage('Recipe dimensions accepted. Update gearbox runs the full 3D and native checks.',
 `Core diameter: ${r.diameter_mm.toFixed(2)} mm\nHeight: ${r.height_mm.toFixed(2)} mm\nCalculated pitch: ${r.resolved_values.contact_pitch_radius.toFixed(2)} mm\n`+JSON.stringify(r.sampling,null,2));
 }catch(error){cadMessage('Cannot build these settings: '+error.message);}finally{cadBusy=false;cadEnable();}};
$('cad-build').onclick=async()=>{cadBusy=true;cadEnable();cadMessage('Starting isolated gearbox update…');try{await cadRequest('/api/build',cadValues());await cadPoll();}catch(error){cadBusy=false;cadEnable();cadMessage('Cannot start: '+error.message);}};
$('cad-load').onclick=async()=>{try{cadLoad(await cadRequest('/api/controls'));cadMessage('Loaded the accepted gearbox settings.');}catch(error){cadMessage(error.message);}};
$('cad-native').onclick=async()=>{cadBusy=true;cadEnable();try{cadLoad(await cadRequest('/api/read-native',{}));cadMessage('Loaded saved native control values. Check or Update to apply them to the whole gearbox.');}catch(error){cadMessage(error.message);}finally{cadBusy=false;cadEnable();}};
cadRequest('/api/controls').then(data=>{cadConnected=true;cadEnable();cadLoad(data);cadMessage('Connected. Change the explorer controls, then Check or Update gearbox.','SolidCraft master: '+data.master);cadPoll();}).catch(()=>{cadEnable();cadMessage('Offline study mode. Run action_gearbox_controls.py in the project folder to enable native builds.');});
