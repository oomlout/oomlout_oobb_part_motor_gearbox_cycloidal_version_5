/* Offline motion screening and portable design-library validation. */
(function(root){
 'use strict';
 const G=root.Cycloid || require('./geometry.js'),VERSION=1;
 const separation=(a,b)=>Math.hypot(a.xy[0]-b.xy[0],a.xy[1]-b.xy[1])-a.r-b.r;
 const cache=new WeakMap();
 function clearances(m,side,angle){
   const l=G.layer(m,side,angle),items=[];
   const add=(gap,label,a,b)=>items.push({gap,label,side,angle,a,b});
   // Hole webs and their distance to the disc edge are invariant under translation.
   if(!cache.has(m))cache.set(m,[]);
   const fixed=cache.get(m);
   if(!fixed[side]){
     const base=G.layer(m,side,0),values=[];
     base.holes.forEach((a,i)=>{
       base.holes.slice(i+1).forEach((b,j)=>values.push({gap:separation(a,b),label:`${a.name} / ${b.name} web`,i,j:i+j+1}));
       values.push({gap:G.distanceToBoundary(a.xy,base.points)-a.r,label:`${a.name} / disc edge`,i});
     });
     fixed[side]=values;
   }
   for(const v of fixed[side])add(v.gap,v.label,l.holes[v.i],v.j===undefined?null:l.holes[v.j]);
   l.contacts.forEach((a,i)=>{
     add(-G.distanceToBoundary(a.xy,l.points)-a.r,`${a.name} / disc`,a);
     l.contacts.slice(i+1).forEach(b=>add(separation(a,b),`${a.name} / ${b.name}`,a,b));
   });
   l.hardware.forEach((a,i)=>{
     l.hardware.slice(i+1).forEach(b=>add(separation(a,b),`${a.name} / ${b.name}`,a,b));
     const h=l.holes[i];
     add(h.r-a.r-Math.hypot(a.xy[0]-h.xy[0],a.xy[1]-h.xy[1]),`${a.name} / its orbit hole`,a,h);
     add(m.boreRadius-Math.hypot(...a.xy)-a.r,`${a.name} / casing wall`,a);
     l.contacts.forEach(b=>add(separation(a,b),`${a.name} / ${b.name}`,a,b));
     if(l.bearing){
       const d=Math.hypot(a.xy[0]-l.centre[0],a.xy[1]-l.centre[1]);
       add(Math.max(l.bearing.bore/2-d-a.r,d-a.r-l.bearing.od/2),`Centre bearing / ${a.name}`,a,{xy:l.centre,r:l.bearing.od/2});
     }
   });
   return items;
 }
 function atAngle(m,angle){
   if(!m.profileValid)throw Error('A regular, non-undercut profile is required for motion screening.');
   return [0,1].flatMap(side=>clearances(m,side,angle)).reduce((a,b)=>b.gap<a.gap?b:a);
 }
 async function scan(m,{onProgress=()=>{},cancelled=()=>false,yieldTask=()=>new Promise(r=>setTimeout(r,0))}={}){
   if(!m.profileValid)throw Error('A regular, non-undercut profile is required for motion screening.');
   let worst=null;
   for(let angle=0;angle<360;angle++){
     if(cancelled())return null;
     const sample=atAngle(m,angle);
     if(!worst || sample.gap<worst.gap-1e-10)worst=sample;
     if(angle%4===3){onProgress(angle+1,360);await yieldTask();}
   }
   if(cancelled())return null;
   return {version:VERSION,step:1,samples:360,gap:worst.gap,angle:worst.angle,side:worst.side,label:worst.label};
 }
 function settings(input){
   if(!input||typeof input!=='object'||Array.isArray(input))throw Error('Missing design settings.');
   const p={...G.defaults};
   for(const k of Object.keys(p))if(Object.hasOwn(input,k))p[k]=input[k];
   if(typeof p.auto!=='boolean')throw Error('Invalid automatic sizing setting.');
   return G.calculate(p).p;
 }
 function result(input){
   if(!input)return null;
   if(input.version!==VERSION||input.samples!==360||input.step!==1||!Number.isFinite(input.gap)||!Number.isInteger(input.angle)||input.angle<0||input.angle>=360||![0,1].includes(input.side)||typeof input.label!=='string'||input.label.length>180)throw Error('Invalid motion result.');
   return {version:VERSION,step:1,samples:360,gap:input.gap,angle:input.angle,side:input.side,label:input.label};
 }
 function library(input){
   if(!input||input.format!=='cycloidal-design-library'||input.version!==VERSION||!Array.isArray(input.designs)||input.designs.length>50)throw Error('Choose a V5 design library with at most 50 designs.');
   return input.designs.map(d=>{
     if(!d||typeof d.name!=='string'||!d.name.trim()||d.name.length>80)throw Error('Each design needs a name of 1–80 characters.');
     return {name:d.name.trim(),settings:settings(d.settings),motion:result(d.motion)};
   });
 }
 const api={VERSION,clearances,atAngle,scan,settings,result,library};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else root.CycloidStudies=api;
})(globalThis);
