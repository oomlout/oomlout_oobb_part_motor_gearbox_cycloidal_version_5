'use strict';
const assert=require('node:assert/strict'),G=require('./dist/geometry.js');
globalThis.Cycloid=G;
const S=require('./dist/studies.js');globalThis.CycloidStudies=S;
require('./dist/diagram.js');
(async()=>{
 const m=G.calculate({});
 const touchingContacts=G.calculate({auto:false,radius:10,ratio:10,eccentricity:.1,roller:5});
 assert.ok(G.overlaps(G.layer(touchingContacts,0),touchingContacts).some(o=>o.type==='contact-pair'));
 assert.ok(S.clearances(touchingContacts,0,0).some(c=>c.label==='Ring contact 1 / Ring contact 2'&&c.gap<0));
 // Signed polygon distances and negative gaps agree with the existing overlap detector.
 assert.equal(G.distanceToBoundary([0,0],[[-1,-1],[1,-1],[1,1],[-1,1]]),1);
 assert.equal(G.distanceToBoundary([2,0],[[-1,-1],[1,-1],[1,1],[-1,1]]),-1);
 for(const p of [{},{topBearing:'6705'},{guidePitch:30,auto:false},{guideRadius:5,postRadius:7}]){
   const model=G.calculate(p);
   for(const angle of [0,37,180,277])for(const side of [0,1]){
     const overlap=G.overlaps(G.layer(model,side,angle),model);
     assert.equal(S.clearances(model,side,angle).some(c=>c.gap< -1e-6),overlap.length>0);
   }
 }
 let progress=0;
 const result=await S.scan(m,{onProgress:n=>progress=n,yieldTask:async()=>{}});
 assert.equal(progress,360);assert.equal(result.samples,360);assert.ok(Math.abs(result.gap-.15)<1e-9);
 assert.ok(Math.abs(S.atAngle(m,result.angle).gap-result.gap)<1e-9);
 const low=G.calculate({clearance:.05});
 const checked=await S.scan(low,{yieldTask:async()=>{}});
 assert.ok(checked.gap>.049&&checked.gap<=.05);
 assert.ok(Math.abs(S.atAngle(low,checked.angle).gap-checked.gap)<1e-9);
 // Identical contacts permute after 360 input degrees, including opposed discs.
 for(const side of [0,1]){
   const a=S.clearances(low,side,23).map(c=>c.gap).sort((a,b)=>a-b);
   const b=S.clearances(low,side,383).map(c=>c.gap).sort((a,b)=>a-b);
   assert.ok(a.every((v,i)=>Math.abs(v-b[i])<1e-9));
 }
 let cancelled=false;
 assert.equal(await S.scan(m,{yieldTask:async()=>{cancelled=true;},cancelled:()=>cancelled}),null);
 await assert.rejects(()=>S.scan(G.calculate({auto:false,radius:30.15})),/non-undercut/);
 const svg=globalThis.CycloidDiagram.render(m,0,{margin:.2}).svg;
 assert.ok(svg.includes('class="clearance-highlight"'));
 assert.ok(!globalThis.CycloidDiagram.render(m,0,{margin:.1}).svg.includes('class="clearance-highlight"'));
 const saved={format:'cycloidal-design-library',version:1,designs:[{name:'<b>Prototype</b>',settings:{...G.defaults,auto:false,radius:35,topBearing:'none',bottomBearing:'6700-open3'},motion:result}]};
 const restored=S.library(JSON.parse(JSON.stringify(saved)));
 assert.equal(restored[0].settings.auto,false);assert.equal(restored[0].settings.radius,35);
 assert.equal(restored[0].settings.topBearing,'none');assert.equal(restored[0].settings.bottomBearing,'6700-open3');
 assert.equal(restored[0].name,'<b>Prototype</b>');assert.equal(restored[0].motion.gap,result.gap);
 for(const invalid of [null,{...saved,version:9},{...saved,designs:Array(51).fill(saved.designs[0])},{...saved,designs:[{...saved.designs[0],name:''}]},{...saved,designs:[{...saved.designs[0],settings:{auto:'yes'}}]},{...saved,designs:[{...saved.designs[0],motion:{...result,angle:360}}]}])assert.throws(()=>S.library(invalid));
 console.log('Motion gaps, both disc planes, 360° symmetry, worst-position jump, cancellation, amber highlights and portable-library validation pass.');
})().catch(e=>{console.error(e);process.exitCode=1;});
