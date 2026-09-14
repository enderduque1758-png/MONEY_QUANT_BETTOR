(function(){
  'use strict';
  function byId(id){return document.getElementById(id)}
  function safeDialog(id){
    var d=byId(id);
    if(!d)return;
    try{if(typeof d.showModal==='function'&&!d.open)d.showModal();else d.setAttribute('open','')}catch(_){d.setAttribute('open','')}
  }
  function boot(){
    document.documentElement.classList.add('mq-interactive');
    var settings=byId('settingsBtn');
    if(settings)settings.addEventListener('click',function(){safeDialog('settings')});
    document.addEventListener('click',function(e){
      var openApi=e.target.closest&&e.target.closest('[data-open-api]');
      if(openApi){e.preventDefault();safeDialog('settings');return}
      var filter=e.target.closest&&e.target.closest('#filterToggle');
      if(filter){e.preventDefault();var side=filter.closest('.side');if(side){side.classList.toggle('open');var mark=filter.querySelector('b');if(mark)mark.textContent=side.classList.contains('open')?'−':'+'}}
      var combos=e.target.closest&&e.target.closest('[data-open-combos]');
      if(combos){var tab=document.querySelector('.tab[data-tab="slips"]');if(tab)tab.click()}
    });
    document.querySelectorAll('button').forEach(function(button){button.style.touchAction='manipulation'});
    window.__MQ_INTERACTION_READY__=true;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();