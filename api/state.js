import {getJson,setJson,mergeJson,persistenceInfo} from '../server/store.js';

function send(res,status,data){res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type','application/json; charset=utf-8');return res.status(status).json(data)}
function safeScope(v){return String(v||'default').toLowerCase().replace(/[^a-z0-9:_-]/g,'').slice(0,80)||'default'}

export default async function handler(req,res){
  try{
    const scope=safeScope(req.query&&req.query.scope);
    const key='mq:state:'+scope;
    if(req.method==='GET') return send(res,200,{ok:true,scope,state:await getJson(key,{}),persistence:persistenceInfo()});
    if(req.method==='POST'){
      const body=typeof req.body==='string'?JSON.parse(req.body||'{}'):(req.body||{});
      const encoded=JSON.stringify(body);
      if(encoded.length>900000)return send(res,413,{error:'Estado demasiado grande'});
      const saved=body.replace===true?await setJson(key,body.state||{}):await mergeJson(key,body.state||body);
      return send(res,200,{ok:true,scope,state:saved,persistence:persistenceInfo()});
    }
    return send(res,405,{error:'Método no permitido'});
  }catch(e){return send(res,500,{error:e.message||String(e),persistence:persistenceInfo()})}
}
