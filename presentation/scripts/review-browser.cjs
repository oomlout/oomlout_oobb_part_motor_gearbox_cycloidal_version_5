/* Headless local preview only; no account or remote page access. */
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const fs = require('node:fs');
const packageRoot = process.env.PLAYWRIGHT_PACKAGE_DIR || 'C:/Users/aaron/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const {chromium} = require(packageRoot);
(async () => {
  const qa=path.resolve(__dirname,'../qa');
  const browser=await chromium.launch({headless:true,channel:'msedge'});
  const reports=[];
  const expected=JSON.parse(fs.readFileSync(path.resolve(qa,'../project.json'),'utf8')).readme.assembly_steps.length;
  for(const [name,width,height] of [['desktop',1280,1000],['mobile',390,900]]) {
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(qa,'readme-preview.html')).href);
    await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete));
    await page.screenshot({path:path.join(qa,`readme-${name}.png`)});
    const parts=page.locator('h2').filter({hasText:'Parts'});
    await parts.scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(qa,`readme-${name}-parts.png`)});
    const assembly=page.locator('h2').filter({hasText:'Assembly'});
    await assembly.scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(qa,`readme-${name}-assembly.png`)});
    const report=await page.evaluate(()=>({
      headings:[...document.querySelectorAll('h2')].map(h=>h.textContent),
      brokenImages:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),
      viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,
      tableScrollWidth:document.querySelector('table').scrollWidth,
      tableClientWidth:document.querySelector('table').clientWidth,
      thumbnails:document.querySelectorAll('li img').length,
    }));
    if(report.brokenImages.length || report.documentWidth>width || report.thumbnails!==expected) throw new Error(JSON.stringify(report));
    reports.push({name,...report});
    await page.close();
  }
  fs.writeFileSync(path.join(qa,'readme-browser.json'),JSON.stringify({status:'PASS',reports},null,2));
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1)});
