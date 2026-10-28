'use strict';
const assert=require('node:assert/strict'),G=require('./dist/geometry.js');
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
const baseline=G.calculate({});
close(baseline.minimumRadius,31.15);close(baseline.p.radius,31.15);
for(const input of [{},{ratio:12},{ratio:16},{ratio:24},{roller:4},{eccentricity:1.1},{postPitch:22},{topBearing:'6708'}]){
 const zero=G.calculate(input),buffered=G.calculate({...input,radiusBuffer:.25});
 close(buffered.minimumRadius,zero.minimumRadius);
 close(buffered.p.radius,zero.p.radius+.25);
 close(buffered.appliedBuffer,.25);
 const previous=zero.minimumRadius-.05;
 assert.ok(previous<Math.max(10,zero.required)-1e-9 || G.convexRadius(zero.n,previous,zero.p.eccentricity)<=zero.p.roller+zero.p.clearance);
 assert.ok(G.convexRadius(zero.n,zero.minimumRadius,zero.p.eccentricity)>zero.p.roller+zero.p.clearance);
}
close(G.calculate({ratio:12,radiusBuffer:.25}).p.radius,29.65);
close(G.calculate({ratio:24,radiusBuffer:.25}).p.radius,37.6);
assert.equal(G.calculate({ratio:12}).limitingFeature,'Standoff-hole envelope');
const manual=G.calculate({auto:false,radius:35,radiusBuffer:2});
close(manual.p.radius,35);close(manual.minimumRadius,31.15);close(manual.appliedBuffer,0);
const rounded=G.calculate({radiusBuffer:.011});close(rounded.p.radius,31.2);close(rounded.appliedBuffer,.05);
const tooBig=G.calculate({radiusBuffer:.5});
close(tooBig.p.radius,31.65);assert.equal(tooBig.checks.find(c=>c.name==='Through 6810 retaining lip').ok,false);
assert.equal(G.calculate({topBearing:'6705',radiusBuffer:2}).checks.find(c=>c.name==='Centre bearings to orbit holes').ok,false);
assert.throws(()=>G.calculate({radiusBuffer:-.1}));
assert.throws(()=>G.calculate({radiusBuffer:NaN}));
assert.throws(()=>G.calculate({ratio:60,eccentricity:2,radiusBuffer:25}));
assert.throws(()=>G.calculate({ratio:60,eccentricity:5}));
console.log('Minimum-radius search, reduction changes, persistent buffer, rounding, manual mode and upper fit limits pass.');
