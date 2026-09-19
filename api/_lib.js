const ODDS_BASE='https://api.the-odds-api.com/v4';
const FOOTBALL_BASE='https://v3.football.api-sports.io';

export function json(res,status,payload){
  res.statusCode=status;
  res.setHeader('content-type','application/json; charset=utf-8');
  res.setHeader('cache-control','no-store');
  res.end(JSON.stringify(payload));
}

export function method(req,res,allowed){
  if(!allowed.includes(req.method)){
    res.setHeader('allow',allowed.join(', '));
    json(res,405,{error:'Método no permitido'});
    return false;
  }
  return true;
}

export async function readBody(req){
  if(req.body && typeof req.body==='object') return req.body;
  let raw='';
  for await (const chunk of req) raw+=chunk;
  if(!raw) return {};
  try{return JSON.parse(raw)}catch{throw new Error('JSON inválido')}
}

export function oddsKey(req){
  return String(req.headers['x-odds-api-key']||process.env.THE_ODDS_API_KEY||'').trim();
}

export function footballKey(req){
  return String(req.headers['x-football-api-key']||process.env.API_FOOTBALL_KEY||'').trim();
}

export function quota(headers){
  const n=v=>v==null?null:Number(v);
  return {
    remaining:n(headers.get('x-requests-remaining')),
    used:n(headers.get('x-requests-used')),
    last:n(headers.get('x-requests-last'))
  };
}

export async function oddsFetch(path,key){
  if(!key) throw Object.assign(new Error('The Odds API no está configurada.'),{status:401});
  const sep=path.includes('?')?'&':'?';
  const r=await fetch(ODDS_BASE+path+sep+'apiKey='+encodeURIComponent(key),{headers:{accept:'application/json'}});
  const text=await r.text();
  let data;
  try{data=text?JSON.parse(text):null}catch{data={message:text||'Respuesta inválida'}};
  if(!r.ok){
    const message=data?.message||data?.error||('The Odds API HTTP '+r.status);
    throw Object.assign(new Error(message),{status:r.status,quota:quota(r.headers)});
  }
  return {data,quota:quota(r.headers)};
}

export async function footballFetch(path,key){
  if(!key) throw Object.assign(new Error('API-Football no está configurada.'),{status:401});
  const r=await fetch(FOOTBALL_BASE+'/'+path.replace(/^\//,''),{
    headers:{'x-apisports-key':key,accept:'application/json'}
  });
  const data=await r.json().catch(()=>({errors:{response:'Respuesta inválida'}}));
  if(!r.ok || (data?.errors && Object.keys(data.errors).length)){
    const first=data?.errors&&Object.values(data.errors)[0];
    throw Object.assign(new Error(String(first||('API-Football HTTP '+r.status))),{status:r.status||502});
  }
  return data;
}

export function normalizeName(v){
  return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\b(fc|cf|afc|sc|ac|club|deportivo|deportes)\b/g,' ').replace(/[^a-z0-9]+/g,' ').trim();
}

export function closestFixture(rows,home,away,targetTime){
  const h=normalizeName(home),a=normalizeName(away),target=new Date(targetTime||0).getTime();
  let best=null,bestScore=-Infinity;
  for(const f of rows||[]){
    const fh=normalizeName(f?.teams?.home?.name),fa=normalizeName(f?.teams?.away?.name);
    let score=0;
    if(fh===h)score+=5;else if(fh.includes(h)||h.includes(fh))score+=3;
    if(fa===a)score+=5;else if(fa.includes(a)||a.includes(fa))score+=3;
    const t=new Date(f?.fixture?.date||0).getTime();
    if(Number.isFinite(target)&&Number.isFinite(t)) score-=Math.min(3,Math.abs(t-target)/86400000);
    if(score>bestScore){best=f;bestScore=score}
  }
  return bestScore>=5?best:null;
}

export function clamp(v,min,max){return Math.max(min,Math.min(max,v))}

export function finished(status){
  return ['FT','AET','PEN'].includes(String(status||'').toUpperCase());
}
