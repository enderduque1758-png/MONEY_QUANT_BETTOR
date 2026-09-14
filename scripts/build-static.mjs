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

const renderStart = main.indexOf('function render(){');
const renderEnd = main.indexOf('\nfunction renderAdvancedMarkets', renderStart);
if(renderStart < 0 || renderEnd < 0) throw new Error('Could not locate render() for pagination optimization');
const optimizedRender = `function eventPagination(page,pages,total,start,end){if(total<=10)return'';var nums='';for(var i=1;i<=pages;i++){var near=i===1||i===pages||Math.abs(i-page)<=1;nums+='<button type="button" class="page-number '+(near?'near ':'')+(i===page?'active':'')+'" data-event-page="'+i+'" aria-label="Página '+i+'">'+i+'</button>'}return'<nav class="event-pagination" aria-label="Paginación de partidos"><span class="page-info">Mostrando '+(start+1)+'–'+end+' de '+total+' partidos</span><div class="page-actions"><button type="button" data-event-page="'+Math.max(1,page-1)+'" '+(page<=1?'disabled':'')+'>Anterior</button>'+nums+'<button type="button" data-event-page="'+Math.min(pages,page+1)+'" '+(page>=pages?'disabled':'')+'>Siguiente</button></div></nav>'}\nfunction render(){if($('feedCount'))$('feedCount').textContent=S.events.length?'('+S.events.length+')':'0';if(S.tab==='markets'){$('content').innerHTML=marketCatalogView();return}if(S.tab==='performance'){$('content').innerHTML=performanceDashboard();return}if(S.tab==='bombs'){$('content').innerHTML=bombs();return}if(S.tab==='slips'){$('content').innerHTML=slips();return}if(S.tab==='playercombo'){$('content').innerHTML=playerCombos();return}if(S.tab==='unique'){$('content').innerHTML=uniqueCombos();return}if(S.tab==='long'){$('content').innerHTML=longSlips();return}if(!S.events.length){$('content').innerHTML='<div class="card empty console-empty"><span class="material-symbols-outlined empty-icon">monitoring</span><h2>Mercado deportivo en vivo</h2><p>Conecta tus motores y consulta el calendario para cargar cuotas, señales y combinadas.</p><button class="btn primary empty-api" type="button" data-open-api="1">Configurar API</button><small>La caché inteligente evita llamadas repetidas y conserva el último análisis en este dispositivo.</small></div>'+topOpportunities();return}var a=filtered(),size=10,pages=Math.max(1,Math.ceil(a.length/size));S.eventPage=Math.max(1,Math.min(Number(S.eventPage)||1,pages));var start=(S.eventPage-1)*size,end=Math.min(a.length,start+size),visible=a.slice(start,end),listHtml=visible.length?'<div class="list">'+visible.map(function(ev,i){return card(ev,start+i)}).join('')+'</div>':'<div class="card empty"><h2>Sin coincidencias</h2></div>';$('content').innerHTML=listHtml+eventPagination(S.eventPage,pages,a.length,start,end)+(S.tab==='events'?topOpportunities():'')}`;
main = main.slice(0, renderStart) + optimizedRender + main.slice(renderEnd);

main = main.replace("$('content').onclick=function(e){", "$('content').onclick=function(e){var pageButton=e.target.closest('[data-event-page]');if(pageButton&&!pageButton.disabled){S.eventPage=Number(pageButton.dataset.eventPage)||1;render();var feed=document.querySelector('.feed-nav');if(feed)feed.scrollIntoView({behavior:'smooth',block:'start'});return}");
main = main.replace("$('search').oninput=render;$('filter').onchange=render;", "$('search').oninput=function(){S.eventPage=1;render()};$('filter').onchange=function(){S.eventPage=1;render()};");
await writeFile(mainPath, main, 'utf8');

const indexPath = new URL('index.html', dist);
let html = await readFile(indexPath, 'utf8');
html = html.replace('<script type="module" src="./src/market-options.js"></script>','');
html = html.replace('<script type="module" src="./src/analytics-ui.js"></script>','');
html = html.replace('<script type="module" src="./src/analytics-v2.js"></script>','');
html = html.replace('<script type="module" src="./src/production-engine.js"></script>','');
html = html.replace('<script type="module" src="./src/integration-core.js"></script>','');
if(!html.includes('font-loader.js'))html=html.replace('</body>','<script type="module" src="./src/font-loader.js"></script>\n</body>');
if(!html.includes('performance-loader.js'))html=html.replace('</body>','<script type="module" src="./src/performance-loader.js"></script>\n</body>');
await writeFile(indexPath, html, 'utf8');

console.log('Static build ready: 10-event pagination + content-visibility + system-font first paint + lazy modules');
