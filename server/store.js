const memory = globalThis.__MQ_SERVER_STATE__ || (globalThis.__MQ_SERVER_STATE__ = new Map());

function env(){
  const url=String(process.env.UPSTASH_REDIS_REST_URL||process.env.KV_REST_API_URL||'').trim();
  const token=String(process.env.UPSTASH_REDIS_REST_TOKEN||process.env.KV_REST_API_TOKEN||'').trim();
  return {url,token,remote:!!(url&&token)};
}

async function command(args){
  const e=env();
  if(!e.remote) return null;
  const r=await fetch(e.url,{method:'POST',headers:{authorization:`Bearer ${e.token}`,'content-type':'application/json'},body:JSON.stringify(args)});
  const text=await r.text(); let data;
  try{data=JSON.parse(text)}catch{data={error:text}}
  if(!r.ok||data.error) throw new Error(data.error||`Redis ${r.status}`);
  return data.result;
}

export function persistenceInfo(){const e=env();return{mode:e.remote?'redis':'ephemeral-memory',durable:e.remote}}

export async function getJson(key,fallback=null){
  const e=env();
  if(e.remote){const raw=await command(['GET',key]);if(raw==null)return fallback;try{return JSON.parse(raw)}catch{return fallback}}
  return memory.has(key)?memory.get(key):fallback;
}

export async function setJson(key,value,ttlSeconds=0){
  const e=env();
  if(e.remote){const args=['SET',key,JSON.stringify(value)];if(ttlSeconds>0)args.push('EX',String(ttlSeconds));await command(args)}
  else memory.set(key,value);
  return value;
}

export async function mergeJson(key,patch){
  const current=await getJson(key,{});const next={...(current&&typeof current==='object'?current:{}),...(patch&&typeof patch==='object'?patch:{})};return setJson(key,next)
}
