import { rm, mkdir, copyFile, cp, readFile, writeFile } from 'node:fs/promises';

const dist = new URL('../dist/', import.meta.url);
const root = new URL('../', import.meta.url);

await rm(dist, { recursive: true, force: true });
await mkdir(new URL('./src/', dist), { recursive: true });
await copyFile(new URL('index.html', root), new URL('index.html', dist));
await cp(new URL('src/', root), new URL('src/', dist), { recursive: true });

const mainPath = new URL('src/main.js', dist);
let main = await readFile(mainPath, 'utf8');
main = main.replace(/^\s*import\s+['"]\.\/styles\.css['"];?\s*/m, '');
main = main.replace("state=noBet?'NO BET':apto?'APTO':'VIGILAR';if(h.state==='watch'&&state==='APTO')state='VIGILAR';", "state=noBet?'NO BET':apto?'APTO':'VIGILAR';if(h.state==='watch'&&state==='APTO')state='VIGILAR';try{var qg=readJson('mq_quality_gate_v1',{});if(qg.state==='blocked')state='NO BET';else if(qg.state==='watch'&&state==='APTO')state='VIGILAR'}catch(_){}");
await writeFile(mainPath, main, 'utf8');

const indexPath = new URL('index.html', dist);
let html = await readFile(indexPath, 'utf8');
html = html.replace('<script type="module" src="./src/market-options.js"></script>','');
html = html.replace('<script type="module" src="./src/analytics-ui.js"></script>','');
html = html.replace('<script type="module" src="./src/analytics-v2.js"></script>','');
html = html.replace('<script type="module" src="./src/production-engine.js"></script>','');
html = html.replace('<script type="module" src="./src/integration-core.js"></script>','');
if(!html.includes('performance-loader.js'))html=html.replace('</body>','<script type="module" src="./src/performance-loader.js"></script>\n</body>');
await writeFile(indexPath, html, 'utf8');

console.log('Static build ready: fast first paint + lazy analytics/production modules');
