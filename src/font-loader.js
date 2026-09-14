(function(){
  var loaded=false;
  function loadExternalFonts(){
    if(loaded)return;loaded=true;
    var pre1=document.createElement('link');pre1.rel='preconnect';pre1.href='https://fonts.googleapis.com';
    var pre2=document.createElement('link');pre2.rel='preconnect';pre2.href='https://fonts.gstatic.com';pre2.crossOrigin='anonymous';
    var css=document.createElement('link');css.rel='stylesheet';css.href='https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;0,800;1,700&family=Inter:wght@400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,400,0,0';
    css.onload=function(){document.documentElement.classList.add('external-fonts-ready')};
    document.head.append(pre1,pre2,css);
  }
  if('requestIdleCallback' in window)requestIdleCallback(loadExternalFonts,{timeout:1800});
  else setTimeout(loadExternalFonts,1200);
})();
