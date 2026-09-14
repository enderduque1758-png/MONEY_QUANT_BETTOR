(function(){
'use strict';
const $=id=>document.getElementById(id);
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,Number(v)||0));
const read=(k,f)=>{try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(f))}catch{return f}};
const fmtPct=v=>Number.isFinite(Number(v))?(Number(v)*100).toFixed(1)+'%':'—';
const fmtAge=ms=>{if(!ms)return'—';const m=Math.max(0,Math.floor(ms/60000));return m<1?'<1 min':m<60?m+' min':Math.floor(m/60)+' h'};

function settledHistory(){return read('mq_history',[]).filter(r=>r&&r.settled&&!r.voided&&Number.isFinite(Number(r.outcome))&&Number.isFinite(Number(r.prob))).sort((a,b)=>new Date(a.kickoff)-new Date(b.kickoff));}
function snapshot(){return read('mq_odds_snapshot_v2',null)||{};}
function quality(){
 const snap=snapshot(),events=Array.isArray(snap.events)?snap.events:[],now=Date.now(),age=snap.at?now-Number(snap.at):Infinity;
 const fresh=age<=20*60000?1:age<=60*60000?.8:age<=2*3600000?.55:age<=6*3600000?.25:0;
 let bookTotal=0,withBooks=0,withContext=0,marketTotal=0;
 events.forEach(e=>{const books=Array.isArray(e.bookmakers)?e.bookmakers:[];if(books.length){withBooks++;bookTotal+=books.length;}books.forEach(b=>marketTotal+=(b.markets||[]).length);if(e.football_prediction&&typeof e.football_prediction==='object')withContext++;});
 const avgBooks=events.length?bookTotal/events.length:0,bookScore=clamp(avgBooks/5),contextScore=events.length?withContext/events.length:0;
 const hist=settledHistory(),sampleScore=clamp(hist.length/120),coverage=events.length?withBooks/events.length:0;
 const score=Math.round((fresh*.30+bookScore*.25+contextScore*.20+sampleScore*.15+coverage*.10)*100);
 return{score,fresh,age,events:events.length,avgBooks,contextScore,hist:hist.length,coverage,marketTotal};
}
function stateClass(n){return n>=80?'good':n>=55?'warn':'bad'};
function mount(){
 const anchor=$('backtestStrip');if(!anchor||$('modelAnalyticsPanel'))return;
 const wrap=document.createElement('section');wrap.id='modelAnalyticsPanel';wrap.className='model-analytics';wrap.innerHTML=`
 <div class="analytics-live-head"><div><strong>LIVE DATA QUALITY</strong><small>Frescura · cobertura · contexto · muestra histórica</small></div><span id="dqState">SIN DATOS</span></div>
 <div class="quality-grid">
  <div class="quality-score"><small>Calidad global</small><b id="dqScore">—</b><div class="quality-meter"><i id="dqMeter"></i></div></div>
  <div><small>Frescura</small><b id="dqFresh">—</b><em id="dqAge">—</em></div>
  <div><small>Casas / evento</small><b id="dqBooks">—</b><em id="dqCoverage">—</em></div>
  <div><small>Contexto fútbol</small><b id="dqContext">—</b><em>API-FOOTBALL</em></div>
  <div><small>Muestra liquidada</small><b id="dqHistory">—</b><em>autoaprendizaje</em></div>
 </div>
 <div class="model-chart-head"><div><strong>MODEL PERFORMANCE · SVG</strong><small>Solo resultados liquidados; ventana móvil de 20 picks</small></div><span id="chartSample">n = 0</span></div>
 <div class="svg-chart-grid">
  <article><header><b>Acierto móvil</b><span id="hitLast">—</span></header><div id="hitChart" class="svg-chart"></div></article>
  <article><header><b>Brier móvil</b><span id="brierLast">—</span></header><div id="brierChart" class="svg-chart"></div></article>
  <article><header><b>ROI acumulado</b><span id="roiLast">—</span></header><div id="roiChart" class="svg-chart"></div></article>
 </div>`;
 anchor.insertAdjacentElement('afterend',wrap);
}
function rolling(rows,size,fn){return rows.map((_,i)=>{const s=rows.slice(Math.max(0,i-size+1),i+1);return fn(s)});}
function svgLine(values,opt={}){
 const clean=values.map(v=>Number.isFinite(Number(v))?Number(v):null);if(!clean.some(v=>v!=null))return'<div class="chart-empty">Esperando datos liquidados.</div>';
 const W=420,H=130,p=18,valid=clean.filter(v=>v!=null),min=opt.min!=null?opt.min:Math.min(...valid),max=opt.max!=null?opt.max:Math.max(...valid),span=Math.max(1e-6,max-min);
 const pts=clean.map((v,i)=>v==null?null:[p+(W-2*p)*(i/Math.max(1,clean.length-1)),H-p-(H-2*p)*((v-min)/span)]).filter(Boolean);
 const path=pts.map((q,i)=>(i?'L':'M')+q[0].toFixed(1)+' '+q[1].toFixed(1)).join(' ');
 const base=opt.zero&&min<0&&max>0?H-p-(H-2*p)*((0-min)/span):null;
 return`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${opt.label||'Gráfica del modelo'}"><line x1="${p}" y1="${H-p}" x2="${W-p}" y2="${H-p}" class="chart-axis"/>${base!=null?`<line x1="${p}" y1="${base}" x2="${W-p}" y2="${base}" class="chart-zero"/>`:''}<path d="${path}" class="chart-line" fill="none"/><circle cx="${pts.at(-1)[0]}" cy="${pts.at(-1)[1]}" r="3.5" class="chart-dot"/></svg>`;
}
function performance(){
 const rows=settledHistory();$('chartSample').textContent='n = '+rows.length;if(!rows.length){$('hitChart').innerHTML=$('brierChart').innerHTML=$('roiChart').innerHTML='<div class="chart-empty">Esperando pronósticos liquidados.</div>';$('hitLast').textContent=$('brierLast').textContent=$('roiLast').textContent='—';return;}
 const hit=rolling(rows,20,s=>s.reduce((a,r)=>a+Number(r.outcome),0)/s.length);
 const brier=rolling(rows,20,s=>s.reduce((a,r)=>a+Math.pow(Number(r.prob)-Number(r.outcome),2),0)/s.length);
 let eq=0;const roi=rows.map(r=>{const price=Number(r.price),p=Number(r.prob),bet=price>1&&p*price>1;if(bet)eq+=Number(r.outcome)===1?price-1:-1;return eq;});
 $('hitLast').textContent=fmtPct(hit.at(-1));$('brierLast').textContent=Number(brier.at(-1)).toFixed(3);$('roiLast').textContent=(roi.at(-1)>=0?'+':'')+roi.at(-1).toFixed(2)+' u';
 $('hitChart').innerHTML=svgLine(hit,{min:0,max:1,label:'Acierto móvil de 20 picks'});$('brierChart').innerHTML=svgLine(brier,{min:0,max:.5,label:'Brier móvil de 20 picks'});$('roiChart').innerHTML=svgLine(roi,{zero:true,label:'ROI acumulado en unidades'});
}
function renderQuality(){const q=quality();$('dqScore').textContent=q.score+' / 100';$('dqMeter').style.width=q.score+'%';$('dqState').textContent=q.score>=80?'ALTA':q.score>=55?'MEDIA':'BAJA';$('dqState').className=stateClass(q.score);$('dqFresh').textContent=Math.round(q.fresh*100)+'%';$('dqAge').textContent='última cuota '+fmtAge(q.age);$('dqBooks').textContent=q.avgBooks.toFixed(1);$('dqCoverage').textContent=Math.round(q.coverage*100)+'% eventos con casas';$('dqContext').textContent=Math.round(q.contextScore*100)+'%';$('dqHistory').textContent=String(q.hist);}
function refresh(){if(!$('modelAnalyticsPanel'))mount();if(!$('modelAnalyticsPanel'))return;renderQuality();performance();}
function boot(){mount();refresh();setInterval(refresh,15000);window.addEventListener('storage',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});const nativeFetch=window.fetch;window.fetch=async function(){const r=await nativeFetch.apply(this,arguments);setTimeout(refresh,250);return r};}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
