'use strict';
const assert=require('node:assert/strict');
const G=require('./dist/geometry.js');
globalThis.Cycloid=G;
require('./dist/diagram.js');
const baseline=G.calculate({});
assert.equal(baseline.reference.id,'6810');
assert.deepEqual(baseline.centreBearings.map(b=>b.id),['6703','6703']);
assert.equal(G.bearings['6700'].width,4);
assert.equal(G.bearings['6700-open3'].width,3);
for(const angle of [0,37,90,180,275,360,719])for(const side of [0,1]){
  assert.equal(G.overlaps(G.layer(baseline,side,angle),baseline).length,0);
}
const changed=G.calculate({guideRadius:2,postRadius:3,guidePitch:20,postPitch:23});
assert.ok(Math.abs(changed.guideHole-3.6)<1e-9);
assert.ok(Math.abs(changed.postHole-4.55)<1e-9);
assert.ok(Math.abs(Math.hypot(...changed.guides[0])-20)<1e-9);
assert.ok(Math.abs(Math.hypot(...changed.posts[0])-23)<1e-9);
const different=G.calculate({topBearing:'6705',bottomBearing:'6701'});
assert.ok(G.overlaps(G.layer(different,0),different).some(o=>o.type==='hole-pair'&&o.label.includes('Centre bearing seat')));
assert.equal(G.overlaps(G.layer(different,1),different).length,0);
const drawing=globalThis.CycloidDiagram.render(different,0,{underlay:true});
assert.ok(drawing.svg.includes('class="overlap-highlight"'));
assert.ok(drawing.svg.includes('layer0-overlap-'));
assert.ok(!drawing.svg.includes('layer1-overlap-'));
const none=G.calculate({topBearing:'none',bottomBearing:'6700-open3'});
assert.equal(none.centreBearings[0],null);
assert.equal(G.layer(none,0).holes.length,9);
assert.equal(none.centreBearings[1].width,3);
const thick=G.calculate({topBearing:'6707'});
assert.equal(thick.checks.find(c=>c.name==='Top bearing retention').ok,false);
assert.equal(thick.checks.find(c=>c.name==='Bottom bearing retention').ok,true);
for(const id of Object.keys(G.bearings)){
  const ref=G.calculate({referenceBearing:id});
  assert.equal(ref.casingRadius,baseline.casingRadius);
  assert.equal(ref.bearingStack,baseline.bearingStack);
  assert.equal(G.overlaps(G.layer(ref,0),ref).length,0);
}
const bodyCollision=G.calculate({guideRadius:5,postRadius:7});
assert.ok(G.overlaps(G.layer(bodyCollision,0),bodyCollision).some(o=>o.type==='hardware-pair'));
const breakout=G.calculate({auto:false,radius:31.15,guidePitch:34});
assert.ok(G.overlaps(G.layer(breakout,0),breakout).some(o=>o.type==='hole-breakout'));
assert.ok(G.overlaps(G.layer(breakout,0),breakout).some(o=>o.type==='hardware-casing'));
assert.equal(G.circleOverlap({xy:[0,0],r:2},{xy:[4,0],r:2}),false);
assert.equal(G.circleOverlap({xy:[0,0],r:2},{xy:[3.9,0],r:2}),true);
assert.throws(()=>G.calculate({topBearing:'fake'}));
assert.throws(()=>G.calculate({postRadius:-1}));
console.log('Radius controls, 26 catalogue entries, independent bearings, axial retention, plane separation and overlap regions pass.');
