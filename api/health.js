import handler from '../server/handler.js';
export default function(req,res){
  if(req.method==='OPTIONS'){
    res.setHeader('Access-Control-Allow-Origin',req.headers.origin||'*');
    res.setHeader('Access-Control-Allow-Methods','GET,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers','Content-Type,X-Odds-Api-Key,X-Football-Api-Key');
    return res.status(204).end();
  }
  req.query={...(req.query||{}),path:'health'};
  return handler(req,res);
}
