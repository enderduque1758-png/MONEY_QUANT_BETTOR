import handler from '../server/handler.js';

export default function(req,res){
  if(req.method==='OPTIONS'){
    const origin=String(req.headers&&req.headers.origin||'');
    if(origin)res.setHeader('Access-Control-Allow-Origin',origin);
    res.setHeader('Vary','Origin');
    res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers','Content-Type,X-Odds-Api-Key,X-Football-Api-Key');
    return res.status(204).end();
  }

  let path=req.query&&req.query.path;
  if(Array.isArray(path))path=path.join('/');
  if(!path){
    const url=String(req.url||'').split('?')[0];
    path=url.replace(/^\/api\/?/,'');
  }
  req.query={...(req.query||{}),path:String(path||'').replace(/^\/+|\/+$/g,'')};
  return handler(req,res);
}
