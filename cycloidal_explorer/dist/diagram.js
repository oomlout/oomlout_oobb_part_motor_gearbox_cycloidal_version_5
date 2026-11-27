/* SVG plan views. Pink is the exact planar intersection, not a whole-part tint. */
(function(root){
 'use strict';
 const G=root.Cycloid,fmt=(v,d=2)=>Number.isFinite(v)?v.toFixed(d):'—';
 const circle=(x,y,r,fill,stroke='none',width=.22,extra='')=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" ${extra}/>`;
 const circleShape=h=>circle(...h.xy,h.r,'white');
 const polygon=points=>'M'+points.map(p=>p.map(v=>v.toFixed(4)).join(',')).join('L')+'Z';
 const annulus=(x,y,ro,ri)=>`M${x-ro},${y}a${ro},${ro} 0 1 0 ${2*ro},0a${ro},${ro} 0 1 0 ${-2*ro},0Z M${x-ri},${y}a${ri},${ri} 0 1 0 ${2*ri},0a${ri},${ri} 0 1 0 ${-2*ri},0Z`;
 function dim(x1,x2,y,label){return `<path d="M${x1},${y-1}v2 M${x2},${y-1}v2 M${x1},${y}H${x2}" fill="none" stroke="#526c68" stroke-width=".18"/><text x="${(x1+x2)/2}" y="${y-1.8}" text-anchor="middle" fill="#365b55" font-size="2.6">${label}</text>`;}
 function bearing(b,x,y,ghost=false){
   if(!b)return '';
   const ro=b.od/2,ri=b.bore/2;
   return `<g ${ghost?'opacity=".38"':''}><path d="${annulus(x,y,ro,ri)}" fill="#cbd7df" fill-rule="evenodd" stroke="#7f949f" stroke-width=".25"/>`+
    circle(x,y,ri+(ro-ri)*.25,'none','#a3b1b8',.16)+circle(x,y,ro-(ro-ri)*.25,'none','#a3b1b8',.16)+'</g>';
 }
 function view(m,l,overlap,underlay,near=[]){
   const uid='layer'+l.side,path=l.points.length?polygon(l.points):'',area=Math.max(m.casingRadius,m.reference.od/2,...l.holes.map(h=>Math.hypot(...h.xy)+h.r))+20;
   let out=`<defs><mask id="${uid}-material" maskUnits="userSpaceOnUse" x="${-area}" y="${-area}" width="${area*2}" height="${area*2}"><rect x="${-area}" y="${-area}" width="${area*2}" height="${area*2}" fill="black"/><path d="${path}" fill="white"/>${l.holes.map(h=>circle(...h.xy,h.r,'black')).join('')}</mask><mask id="${uid}-outside" maskUnits="userSpaceOnUse" x="${-area}" y="${-area}" width="${area*2}" height="${area*2}"><rect x="${-area}" y="${-area}" width="${area*2}" height="${area*2}" fill="white"/><path d="${path}" fill="black"/></mask>`;
   if(l.bearing)out+=`<clipPath id="${uid}-bearing"><path d="${annulus(...l.centre,l.bearing.od/2,l.bearing.bore/2)}" clip-rule="evenodd"/></clipPath>`;
   out+=`<clipPath id="${uid}-casing"><path d="${annulus(0,0,m.casingRadius,m.boreRadius)}" clip-rule="evenodd"/></clipPath></defs>`;
   out+=circle(0,0,m.casingRadius,'#ece6d8','#9b8a6c',.3)+circle(0,0,m.boreRadius,'#fcfcf8','#9b8a6c');
   if(underlay)out+=bearing(m.reference,0,0,true);
   out+=circle(0,0,m.p.radius,'none','#aeb5a7',.18,'stroke-dasharray="1.2 1.2"');
   out+=l.contacts.map(h=>circle(...h.xy,h.r,'#d7ad6e','#8b7047')).join('');
   if(path)out+=`<path d="${path}" fill="${m.profileValid?'#c4ddd1':'#f3ccc0'}" fill-opacity=".88" stroke="#197f76" stroke-width=".28"/>`;
   out+=l.holes.map(h=>circle(...h.xy,h.r,'#fcfcf8','#197f76')).join('');
   out+=bearing(l.bearing,...l.centre);
   out+=l.hardware.map((h,i)=>circle(...h.xy,h.r,i<6?'#345852':'#869d91','#526e62')+(i>=6?circle(...h.xy,1.5,'#fcfcf8','#526e62',.15):'')).join('');
   // Underlay boundaries stay visible as dashed references, even under the disc.
   if(underlay)out+=`<g opacity=".45">${[m.reference.od/2,m.reference.bore/2].map(r=>circle(0,0,r,'none','#748b99',.2,'stroke-dasharray="1.4 1.4"')).join('')}</g>`;
   overlap.forEach((o,i)=>{
     const pink=circle(...o.a.xy,o.a.r,'#ff39a0','none',0,'fill-opacity=".85"');
     const title=`<title>${o.label}</title>`;
     if(o.b){const id=`${uid}-overlap-${i}`;out+=`<defs><clipPath id="${id}">${circleShape(o.b)}</clipPath></defs><g class="overlap-highlight" clip-path="url(#${id})">${title}${pink}</g>`;}
     else if(o.type==='hole-breakout')out+=`<g class="overlap-highlight" mask="url(#${uid}-outside)">${title}${pink}</g>`;
     else if(o.type==='contact-disc')out+=`<g class="overlap-highlight" mask="url(#${uid}-material)">${title}${pink}</g>`;
     else if(o.type==='bearing-hardware')out+=`<g class="overlap-highlight" clip-path="url(#${uid}-bearing)">${title}${pink}</g>`;
     else if(o.type==='hardware-casing')out+=`<g class="overlap-highlight" clip-path="url(#${uid}-casing)">${title}${pink}</g>`;
   });
   const marked=new Set();
   for(const item of near)for(const shape of [item.a,item.b].filter(Boolean)){
     const key=shape.xy.join(',')+':'+shape.r;
     if(marked.has(key))continue;marked.add(key);
     out+=`<g class="clearance-highlight"><title>${item.label}: ${fmt(item.gap,3)} mm gap</title>${circle(...shape.xy,shape.r,'none','#c3830c',.55,'stroke-dasharray="1 .6"')}</g>`;
   }
   out+=`<path d="M-4,0H4 M0,-4V4" fill="none" stroke="#728b80" stroke-width=".15"/><path d="M0,0L${l.centre.join(',')}" stroke="#dc6947" stroke-width=".45"/>`+circle(...l.centre,.5,'#dc6947');
   return out;
 }
 function render(m,angle,options={}){
   const layers=[G.layer(m,0,angle),G.layer(m,1,angle)],overlaps=layers.map(l=>G.overlaps(l,m));
   const near=layers.map((l,i)=>root.CycloidStudies&&m.profileValid&&options.margin>0?root.CycloidStudies.clearances(m,i,angle).filter(c=>c.gap>=-1e-6&&c.gap<options.margin):[]);
   const extent=Math.max(m.casingRadius,options.underlay?m.reference.od/2:0,...layers.flatMap(l=>l.holes.map(h=>Math.hypot(...h.xy)+h.r)))+2;
   const spacing=2*extent+18,ro=m.reference.od/2,refY=extent+ro+32,refX=spacing/2;
   const left=-extent-8,right=spacing+extent+8,top=-extent-24,bottom=refY+ro+24,w=right-left,h=bottom-top;
   let svg=`<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="svgtitle svgdesc" width="${w}mm" height="${h}mm" viewBox="${left} ${top} ${w} ${h}" font-family="Arial,sans-serif"><title id="svgtitle">Top and bottom cycloids with ${m.reference.name} bearing reference</title><desc id="svgdesc">${m.n}:1 casing output. Pink shows intersecting holes or hardware in each individual plane. Reference bearing is not collision-tested.</desc>`;
   layers.forEach((l,i)=>{
     svg+=`<g transform="translate(${i*spacing},0)"><text x="0" y="${-extent-17}" text-anchor="middle" font-size="3.5" font-weight="bold" fill="#183d3b">${i?'BOTTOM':'TOP'} CYCLOID</text><text x="0" y="${-extent-11}" text-anchor="middle" font-size="2.6" fill="#697571">${l.bearing?l.bearing.name+' · '+l.bearing.bore+' × '+l.bearing.od+' × '+l.bearing.width:'No centre bearing'}</text>`;
     svg+=view(m,l,overlaps[i],options.underlay,near[i])+dim(-m.casingRadius,m.casingRadius,extent+5,`Casing Ø${fmt(2*m.casingRadius)}`);
     svg+=`<text x="0" y="${extent+12}" text-anchor="middle" font-size="2.6" fill="${overlaps[i].length?'#be2673':'#197f76'}">${overlaps[i].length?overlaps[i].length+' planar overlaps':'No planar overlaps'}</text></g>`;
   });
   svg+=bearing(m.reference,refX,refY)+`<text x="${refX}" y="${refY-ro-7}" text-anchor="middle" font-size="3" fill="#183d3b">${m.reference.name} · REFERENCE AT THE SAME SCALE</text>`;
   svg+=dim(refX-ro,refX+ro,refY+ro+6,`OD ${m.reference.od} · bore ${m.reference.bore} · width ${m.reference.width} mm`);
   svg+=`<text x="${refX}" y="${refY+ro+14}" text-anchor="middle" font-size="2.5" fill="#697571">Separate axial plane / scale reference only</text>`;
   svg+=`<path d="M${left+4},${bottom-8}h20 m-20,-1v2 m20,-2v2" stroke="#365b55" stroke-width=".35"/><text x="${left+14}" y="${bottom-3}" text-anchor="middle" fill="#365b55" font-size="2.4">20 mm</text><text x="${refX}" y="${bottom-2}" text-anchor="middle" fill="#365b55" font-size="2.3">${m.p.auto?`Pitch R: minimum ${fmt(m.minimumRadius)} + buffer ${fmt(m.appliedBuffer)} = ${fmt(m.p.radius)} mm`:`Manual pitch R ${fmt(m.p.radius)} mm · minimum ${fmt(m.minimumRadius)} mm`}</text></svg>`;
   return {svg,overlaps};
 }
 root.CycloidDiagram={render};
})(globalThis);
