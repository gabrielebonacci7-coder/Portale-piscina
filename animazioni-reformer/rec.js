const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();
for(const v of process.argv.slice(2)){
 const dir='out'+v;fs.rmSync(dir,{recursive:true,force:true});
 const ctx=await b.newContext({viewport:{width:1080,height:1080},recordVideo:{dir,size:{width:1080,height:1080}}});
 const p=await ctx.newPage();p.on('pageerror',e=>console.log(v,'ERR',e.message));const t0=Date.now();
 await p.goto('file://'+process.cwd()+'/anim.html?v='+v);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(1200);
 const lead=(Date.now()-t0)/1000;const d=await p.evaluate(()=>window.play());await p.waitForTimeout(d*1000+300);
 await ctx.close();fs.writeFileSync(dir+'/lead.txt',String(lead));console.log(v,'dur',d.toFixed(1));}
await b.close();})();
