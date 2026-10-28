/* Pure geometry shared by the page, regression tests and PDF data export.
   Port of gearbox_native/cycloid_equation.py and V5 radial envelope rules. */
(function (root) {
  'use strict';
  const TAU = 2 * Math.PI;
  // Nominal d x D x B. The catalogue sources and the 6700 width variant are
  // documented in the page; these values are bundled for offline use.
  const bearings=Object.fromEntries([
    ['6700',10,15,4],['6700-open3',10,15,3],['6701',12,18,4],['6702',15,21,4],
    ['6703',17,23,4],['6704',20,27,4],['6705',25,32,4],['6706',30,37,4],
    ['6707',35,44,5],['6708',40,50,6],['6709',45,55,6],['6710',50,62,6],['6711',55,68,7],
    ['6800',10,19,5],['6801',12,21,5],['6802',15,24,5],['6803',17,26,5],
    ['6804',20,32,7],['6805',25,37,7],['6806',30,42,7],['6807',35,47,7],
    ['6808',40,52,7],['6809',45,58,7],['6810',50,65,7],['6811',55,72,9],['6812',60,78,10]
  ].map(([id,bore,od,width])=>[id,{id,name:id==='6700-open3'?'6700 open (3 mm)':id,bore,od,width,series:id.startsWith('67')?'6700':'6800'}]));
  const defaults = {ratio:20, radius:31.15, radiusBuffer:0, eccentricity:1.4, roller:3, clearance:.2, wall:2, thickness:5, gap:.5, auto:true,
    guideRadius:1.5,guidePitch:17.4,postRadius:2.7,postPitch:18.55,referenceBearing:'6810',topBearing:'6703',bottomBearing:'6703'};
  const presets = [
    {name:'Current V5', note:'The active 20:1 design: 3 mm printed contacts and 1.4 mm eccentricity.', values:{...defaults}},
    {name:'12:1 exploration', note:'Fewer, broader lobes with the same contacts and orbit. V5 radial interfaces retained.', values:{...defaults,ratio:12}},
    {name:'30:1 exploration', note:'A smaller orbit and 2 mm contacts keep the higher contact count compact.', values:{...defaults,ratio:30,eccentricity:.9,roller:2}},
    {name:'Smaller-contact study', note:'A 20:1 study inspired by the earlier 1.65 mm contact / 1.25 mm orbit iterations.', values:{...defaults,eccentricity:1.25,roller:1.65}},
  ];
  function convexRadius(n,r,e) {
    if (!(r>n*e && e>0)) return NaN;
    const a=r*r+n*n*e*e,b=2*n*r*e,c=r*r+n**3*e*e,d=n*(n+1)*r*e;
    const u=Math.max(-1,Math.min(1,(3*b*c-2*d*a)/(b*d)));
    return 1/Math.max(...[-1,1,u].map(v=>(c-d*v)/(a-b*v)**1.5));
  }
  function point(n,r,e,a,t) {
    const u=r*Math.cos(t)-n*e*Math.cos(n*t),v=r*Math.sin(t)-n*e*Math.sin(n*t),s=Math.hypot(u,v);
    return [r*Math.cos(t)-e*Math.cos(n*t)-a*u/s,r*Math.sin(t)-e*Math.sin(n*t)-a*v/s];
  }
  function positions(r,n,phase=0) {return Array.from({length:n},(_,i)=>[r*Math.cos(phase+i*TAU/n),r*Math.sin(phase+i*TAU/n)]);}
  function profilePoints(n,r,e,a,tolerance=.0005) {
    const points=[],count=(n-1)*24,at=t=>point(n,r,e,a,t);
    function distance(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],norm=dx*dx+dy*dy;
      const u=norm?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/norm)):0;
      return Math.hypot(p[0]-a[0]-u*dx,p[1]-a[1]-u*dy);}
    function segment(t0,p0,t1,p1,depth=0){
      const error=Math.max(...[.25,.5,.75].map(u=>distance(at(t0+(t1-t0)*u),p0,p1)));
      if(error>tolerance && depth<12){const tm=(t0+t1)/2,pm=at(tm);segment(t0,p0,tm,pm,depth+1);segment(tm,pm,t1,p1,depth+1);}
      else points.push(p0);
    }
    for(let i=0;i<count;i++){const t0=TAU*i/count,t1=TAU*(i+1)/count;segment(t0,at(t0),t1,at(t1));}
    return points;
  }
  function calculate(input) {
    const p={...defaults,...input};
    const bounds={ratio:[3,60],radius:[10,150],radiusBuffer:[0,25],eccentricity:[.1,5],roller:[.3,10],clearance:[0,1],wall:[.8,6],thickness:[2,12],gap:[.1,3],
      guideRadius:[.5,6],guidePitch:[3,70],postRadius:[1.7,12],postPitch:[3,70]};
    for (const [key,[min,max]] of Object.entries(bounds)) {
      if (!Number.isFinite(p[key]) || p[key]<min || p[key]>max) throw Error(`${key} must be between ${min} and ${max}.`);
    }
    if (!Number.isInteger(p.ratio)) throw Error('Reduction must be a whole number of ring contacts.');
    for(const key of ['referenceBearing','topBearing','bottomBearing']){
      if(!(key!=='referenceBearing' && p[key]==='none') && !Object.hasOwn(bearings,p[key]))throw Error('Choose a bearing from the catalogue.');
    }
    const reference=bearings[p.referenceBearing],centreBearings=[bearings[p.topBearing]||null,bearings[p.bottomBearing]||null];
    const seats=centreBearings.map(b=>b?b.od/2+.1:0),largestSeat=Math.max(...seats);
    const n=p.ratio,e=p.eccentricity,a=p.roller+p.clearance;
    const guideHole=p.guideRadius+e+.2, postHole=p.postRadius+e+.15;
    const limits={ 'Profile coefficient':n*e/.9, 'Guide-hole envelope':p.guidePitch+guideHole+2+e+a,
      'Standoff-hole envelope':p.postPitch+postHole+2+e+a, 'Contact spacing':(p.roller+1)/Math.sin(Math.PI/n),
      'Centre-bearing envelope':largestSeat+2+e+a };
    const required=Math.max(...Object.values(limits));
    // Find the first 0.05 mm pitch step satisfying every lower radius bound,
    // then the analytic undercut condition. Buffer is added AFTER this search.
    const firstStep=Math.ceil((Math.max(10,required)-1e-10)/.05);
    let minimumStep=firstStep;
    while(minimumStep<=3000 && !(convexRadius(n,minimumStep/20,e)>a))minimumStep++;
    const minimumRadius=minimumStep<=3000?minimumStep/20:null;
    const limitingFeature=minimumStep>firstStep?'Analytic undercut':required<10?'Explorer radius range':Object.keys(limits).reduce((a,b)=>limits[a]>=limits[b]?a:b);
    if(p.auto && minimumRadius===null)throw Error('No automatic pitch radius at or below 150 mm satisfies these settings. Reduce the ratio, eccentricity or contact radius.');
    const r=p.auto?Math.ceil((minimumRadius+p.radiusBuffer-1e-10)*20)/20:p.radius;
    if(r>150)throw Error('The minimum radius plus buffer exceeds 150 mm. Reduce the buffer or geometry size.');
    const appliedBuffer=p.auto?r-minimumRadius:0;
    // The fixed casing lip also gives an UPPER radius bound. More buffer can
    // exceed it, so retain the requested geometry and report the failure.
    const maximumLipRadius=31.2-.05-2*e+a;
    const rho=convexRadius(n,r,e), singular=r<=n*e;
    const points=singular ? [] : profilePoints(n,r,e,a);
    const radii=points.map(([x,y])=>Math.hypot(x,y));
    const rootRadius=singular?NaN:radii.reduce((v,x)=>Math.min(v,x),Infinity), tipRadius=singular?NaN:radii.reduce((v,x)=>Math.max(v,x),0);
    const casingRadius=Math.max(r+p.roller+p.wall,32.5+.1+p.wall);
    const sweptRadius=r+2*e-a, boreRadius=r+Math.max(0,2*e-p.roller);
    const guides=positions(p.guidePitch,6,Math.PI/6), posts=positions(p.postPitch,3);
    const holes=[...guides.map((xy,i)=>({xy,r:guideHole,name:`Guide hole ${i+1}`})),...posts.map((xy,i)=>({xy,r:postHole,name:`Standoff hole ${i+1}`}))];
    let betweenHoles=Infinity;
    holes.forEach((h,i)=>holes.slice(i+1).forEach(k=>{betweenHoles=Math.min(betweenHoles,Math.hypot(h.xy[0]-k.xy[0],h.xy[1]-k.xy[1])-h.r-k.r);}));
    const checks=[]; const add=(name,ok,value,explanation)=>checks.push({name,ok,value,explanation});
    add('Regular centre curve',!singular,`Ne/R = ${(n*e/r).toFixed(3)}`,'R must exceed N × eccentricity.');
    add('No analytic undercut',!singular && a<rho,Number.isFinite(rho)?`${(rho-a).toFixed(3)} mm margin`:'Undefined at singular curve','Contact radius + clearance must be below the minimum convex radius.');
    add('V5 radial feature envelopes',r>=required-1e-8,`${(r-required).toFixed(2)} mm margin`,'Includes 2 mm feature webs, contact spacing and the 0.90 coefficient limit.');
    add('Casing contact attachment',r+p.roller-boreRadius>=.4-1e-8,`${(r+p.roller-boreRadius).toFixed(2)} mm`,'Printed contacts need at least 0.40 mm radial attachment.');
    const driveWeb=Math.min(p.guidePitch-guideHole-largestSeat,p.postPitch-postHole-largestSeat);
    add('Centre bearings to orbit holes',driveWeb>=2-1e-8,`${driveWeb.toFixed(2)} mm web`,'The larger selected centre-bearing seat needs at least 2 mm to the orbit holes.');
    add('Between orbit holes',betweenHoles>=2-1e-8,`${betweenHoles.toFixed(2)} mm web`,'Checks all six guide holes and three standoff holes.');
    add('Through 6810 retaining lip',31.2-sweptRadius>=.05-1e-8,`${(31.2-sweptRadius).toFixed(2)} mm radial gap`,'V5 lip is Ø62.4. The orbiting disc envelope needs 0.05 mm insertion clearance.');
    centreBearings.forEach((b,i)=>add(`${i?'Bottom':'Top'} bearing retention`,!b||p.thickness>=b.width+1-1e-8,
      b?`${p.thickness.toFixed(2)} / ${(b.width+1).toFixed(2)} mm needed`:'No bearing selected',
      b?`${b.name}: ${b.width} mm width + 0.20 mm axial allowance + 0.80 mm retaining lip.`:'No centre seat is cut in this study; a drive interface still needs designing.'));
    add('Fixed hardware inside V5 carriers',Math.max(p.guidePitch+p.guideRadius,p.postPitch+p.postRadius)<=24.9,
      `${(24.9-Math.max(p.guidePitch+p.guideRadius,p.postPitch+p.postRadius)).toFixed(2)} mm margin`,
      'The retained 6810 carrier journal radius is 24.9 mm. The reference bearing selector is for scale only.');
    add('Standoff screw-bore wall',p.postRadius-1.7>=.8-1e-8,`${(p.postRadius-1.7).toFixed(2)} mm wall`,'The retained Ø3.4 M3 passage needs at least 0.80 mm of material.');
    return {p:{...p,radius:r},n,lobes:n-1,points,rho,rootRadius,tipRadius,casingRadius,sweptRadius,boreRadius,guideHole,postHole,guides,posts,limits,required,checks,
      minimumRadius,limitingFeature,appliedBuffer,maximumLipRadius,
      holes,centreBearings,seats,reference,
      valid:checks.every(c=>c.ok), profileValid:!singular&&a<rho, bearingStack:14+2*p.thickness+p.gap};
  }
  function circleOverlap(a,b){return Math.hypot(a.xy[0]-b.xy[0],a.xy[1]-b.xy[1])<a.r+b.r-1e-7;}
  function distanceToBoundary(xy,points){let min=Infinity,inside=false;
    for(let i=0,j=points.length-1;i<points.length;j=i++){
      const a=points[j],b=points[i],dx=b[0]-a[0],dy=b[1]-a[1],norm=dx*dx+dy*dy;
      const u=norm?Math.max(0,Math.min(1,((xy[0]-a[0])*dx+(xy[1]-a[1])*dy)/norm)):0;
      const ex=xy[0]-a[0]-u*dx,ey=xy[1]-a[1]-u*dy;
      min=Math.min(min,ex*ex+ey*ey);
      if((a[1]>xy[1])!==(b[1]>xy[1]) && xy[0]<(b[0]-a[0])*(xy[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
    }return (inside?1:-1)*Math.sqrt(min);
  }
  function layer(m,side,angle=0){
    const phase=angle*Math.PI/180+side*Math.PI,rot=-side*Math.PI/m.lobes,co=Math.cos(rot),si=Math.sin(rot);
    const centre=[m.p.eccentricity*Math.cos(phase),m.p.eccentricity*Math.sin(phase)];
    const points=m.points.map(([x,y])=>[x*co-y*si+centre[0],x*si+y*co+centre[1]]);
    const holes=[...m.holes,...(m.seats[side]?[{xy:[0,0],r:m.seats[side],name:'Centre bearing seat'}]:[])].map(h=>({...h,xy:[h.xy[0]+centre[0],h.xy[1]+centre[1]]}));
    const hardware=[...m.guides.map((xy,i)=>({xy,r:m.p.guideRadius,name:`Static screw ${i+1}`})),...m.posts.map((xy,i)=>({xy,r:m.p.postRadius,name:`Standoff ${i+1}`}))];
    const contacts=positions(m.p.radius,m.n,angle*Math.PI/180/m.n).map((xy,i)=>({xy,r:m.p.roller,name:`Ring contact ${i+1}`}));
    return {side,centre,points,holes,hardware,contacts,bearing:m.centreBearings[side]};
  }
  function overlaps(layer,m){
    const result=[];
    const pairs=(items,type)=>items.forEach((a,i)=>items.slice(i+1).forEach(b=>{if(circleOverlap(a,b))result.push({type,a,b,label:`${a.name} / ${b.name}`});}));
    pairs(layer.holes,'hole-pair');pairs(layer.hardware,'hardware-pair');pairs(layer.contacts,'contact-pair');
    if(layer.points.length){
      for(const h of layer.holes)if(distanceToBoundary(h.xy,layer.points)<h.r-1e-6)result.push({type:'hole-breakout',a:h,label:`${h.name} breaks through disc edge`});
      for(const h of layer.contacts)if(distanceToBoundary(h.xy,layer.points)>-h.r+1e-6)result.push({type:'contact-disc',a:h,label:`${h.name} / disc`});
    }
    // Bearing annulus is hardware; the empty bore itself is not a collision.
    if(layer.bearing)for(const h of layer.hardware){const d=Math.hypot(h.xy[0]-layer.centre[0],h.xy[1]-layer.centre[1]);
      if(d-h.r<layer.bearing.od/2-1e-6 && d+h.r>layer.bearing.bore/2+1e-6)result.push({type:'bearing-hardware',a:h,label:`Centre bearing / ${h.name}`});}
    for(const h of layer.hardware){
      if(Math.hypot(...h.xy)+h.r>m.boreRadius+1e-6)result.push({type:'hardware-casing',a:h,label:`${h.name} / casing wall`});
      for(const k of layer.contacts)if(circleOverlap(h,k))result.push({type:'hardware-contact',a:h,b:k,label:`${h.name} / ${k.name}`});
    }
    return result;
  }
  const api={defaults,presets,bearings,calculate,point,profilePoints,convexRadius,positions,circleOverlap,distanceToBoundary,layer,overlaps};
  if (typeof module!=='undefined' && module.exports) module.exports=api;
  else root.Cycloid=api;
})(typeof globalThis!=='undefined'?globalThis:this);
