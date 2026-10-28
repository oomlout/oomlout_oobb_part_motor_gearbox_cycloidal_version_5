const fs=require('node:fs');
const G=require('./dist/geometry.js');
const examples=G.presets.map(p=>({...p,model:G.calculate(p.values)}));
const rejected=G.calculate({...G.defaults,auto:false,radius:30.15});
fs.mkdirSync('qa',{recursive:true});
fs.writeFileSync('qa/examples.json',JSON.stringify({examples,rejected}));
