import {access,readFile} from 'node:fs/promises';
const required=['dist/index.html','dist/src/main.js','dist/src/analytics-v2.js','dist/src/market-options.js','dist/src/production-engine.js','dist/src/integration-core.js','api/health.js','api/sports.js','api/odds.js','api/state.js','api/settle.js','api/closing-line.js','api/preflight.js','server/store.js','server/settlement.js','server/model-policy.js'];
const missing=[];for(const f of required){try{await access(f)}catch{missing.push(f)}}if(missing.length){console.error('Missing production files:',missing.join(', '));process.exit(1)}
const html=await readFile('dist/index.html','utf8');for(const s of ['main.js','analytics-v2.js','market-options.js','production-engine.js','integration-core.js']){if(!html.includes(s)){console.error('Missing script in dist/index.html:',s);process.exit(1)}}
await import(new URL('../server/model-policy.js',import.meta.url));await import(new URL('../server/settlement.js',import.meta.url));await import(new URL('../server/store.js',import.meta.url));
console.log('Production smoke OK:',required.length,'files + advanced analytics + forced integration + server imports');
