const idle=(fn,timeout=1200)=>{if('requestIdleCallback'in window)requestIdleCallback(fn,{timeout});else setTimeout(fn,Math.min(timeout,500))};
const load=(name)=>import(`./${name}`).catch(err=>console.warn('[lazy]',name,err?.message||err));

// Mantener la UI principal libre: main.js ya renderiza la consola y carga partidos.
idle(()=>load('market-options.js'),500);

// Motores de producción después del primer render, evitando competir con la carga inicial.
idle(()=>load('production-engine.js'),1200);
idle(()=>load('integration-core.js'),1600);

let analyticsLoaded=false;
const loadAnalytics=()=>{if(analyticsLoaded)return;analyticsLoaded=true;load('analytics-v2.js')};
const drawer=document.querySelector('.analytics-drawer');
if(drawer){drawer.addEventListener('toggle',()=>{if(drawer.open)loadAnalytics()},{once:true})}
// Fallback: precargar analítica cuando el navegador esté ocioso.
idle(loadAnalytics,3500);

// Carga anticipada al primer gesto del usuario sin bloquear el arranque.
for(const ev of ['pointerdown','keydown','touchstart'])window.addEventListener(ev,()=>{idle(()=>load('market-options.js'),100);},{once:true,passive:true});
