(function(){
'use strict';
var KEY='mq_extra_markets';
var grid=document.getElementById('extraMarketGrid');
var count=document.getElementById('extraMarketCount');
var save=document.getElementById('saveExtraMarkets');
var clear=document.getElementById('clearExtraMarkets');
if(!grid)return;

var style=document.createElement('style');
style.textContent=`
.extra-market-picker{margin:10px 0;border:1px solid rgba(77,208,225,.2);border-radius:8px;background:rgba(5,18,25,.72);overflow:hidden}
.extra-market-picker>summary{list-style:none;cursor:pointer;min-height:42px;padding:0 10px;display:flex;align-items:center;justify-content:space-between;gap:10px;color:#e9fbff;font-size:.73rem;font-weight:800}
.extra-market-picker>summary::-webkit-details-marker{display:none}
.extra-market-picker>summary span{display:flex;align-items:center;gap:7px}.extra-market-picker>summary .material-symbols-outlined{font-size:18px;color:#48d5e7}
.extra-market-picker>summary b{font-size:.62rem;color:#8feaf4;background:rgba(72,213,231,.09);border:1px solid rgba(72,213,231,.18);padding:5px 7px;border-radius:999px;white-space:nowrap}
.extra-market-body{padding:9px;border-top:1px solid rgba(77,208,225,.12)}
.extra-market-note{margin:0 0 8px;color:#87a1aa;font-size:.64rem;line-height:1.45}
.extra-market-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.extra-market-grid label{min-height:31px;display:flex;align-items:center;gap:6px;padding:6px 7px;border:1px solid rgba(255,255,255,.06);border-radius:6px;background:rgba(255,255,255,.025);font-size:.67rem;color:#b8c9ce;cursor:pointer}
.extra-market-grid label:has(input:checked){border-color:rgba(72,213,231,.35);background:rgba(72,213,231,.08);color:#eaffff}
.extra-market-grid input{accent-color:#43cddd}
.extra-market-actions{display:flex;justify-content:flex-end;gap:6px;margin-top:9px}.extra-market-actions .btn{min-height:32px;padding:0 10px;font-size:.65rem}
@media(max-width:620px){.extra-market-grid{grid-template-columns:1fr}.extra-market-picker>summary{font-size:.68rem}}
`;
document.head.appendChild(style);

function load(){try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(_){return[]}}
function selected(){return Array.from(grid.querySelectorAll('input:checked')).map(function(x){return x.value})}
function paint(values){var set=new Set(values||[]);grid.querySelectorAll('input').forEach(function(x){x.checked=set.has(x.value)});updateCount()}
function updateCount(){var n=selected().length;if(count)count.textContent=n?(n+' activo'+(n===1?'':'s')):'0 activos'}
function persist(){var values=selected();localStorage.setItem(KEY,JSON.stringify(values));updateCount();var s=document.getElementById('status');if(s&&values.length)s.textContent='Mercados avanzados guardados · '+values.length+' favoritos';return values}

paint(load());
grid.addEventListener('change',updateCount);
if(save)save.addEventListener('click',function(){persist();var d=document.getElementById('extraMarketPicker');if(d)d.open=false});
if(clear)clear.addEventListener('click',function(){paint([]);localStorage.removeItem(KEY)});

function applyToAdvanced(){var fav=new Set(load()),adv=document.querySelector('#advanced .advanced-grid');if(!adv||!fav.size)return;adv.querySelectorAll('input[type="checkbox"]').forEach(function(x){if(fav.has(x.value)&&!x.disabled)x.checked=true})}
var advanced=document.getElementById('advanced');
if(advanced){
  advanced.addEventListener('toggle',applyToAdvanced);
  new MutationObserver(function(){if(advanced.open)applyToAdvanced()}).observe(advanced,{childList:true,subtree:true});
}

// Capture any dynamically generated advanced market selector even if the dialog is opened programmatically.
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.adv-btn,[data-advanced],[data-open-advanced]');if(b)setTimeout(applyToAdvanced,40)});
})();
