function send(res,status,data){res.status(status).json(data)}
function multipliers(outcome,odds){
  const p=Number(odds)>1?Number(odds):2;
  if(outcome==='win')return{returnMultiplier:p,profitMultiplier:p-1};
  if(outcome==='loss')return{returnMultiplier:0,profitMultiplier:-1};
  if(outcome==='push'||outcome==='void')return{returnMultiplier:1,profitMultiplier:0};
  if(outcome==='half-win')return{returnMultiplier:(p+1)/2,profitMultiplier:(p-1)/2};
  return{returnMultiplier:.5,profitMultiplier:-.5};
}
function simple(v){return v>1e-9?'win':v<-1e-9?'loss':'push'}
function split(line){const x=Number(line),d=x*2;return Math.abs(d-Math.round(d))<1e-9?[x]:[x-.25,x+.25]}
function combine(parts){
  if(parts.length===1)return parts[0];
  const w=parts.filter(x=>x==='win').length,l=parts.filter(x=>x==='loss').length,p=parts.filter(x=>x==='push').length;
  if(w===2)return'win';if(l===2)return'loss';if(p===2)return'push';
  if(w===1&&p===1)return'half-win';if(l===1&&p===1)return'half-loss';
  return'push';
}
function asian(b){
  if(b.voided)return{market:'asian_handicap',outcome:'void',...multipliers('void',b.odds),components:[{line:Number(b.line),outcome:'void'}]};
  const side=String(b.side),margin=side==='home'?Number(b.homeScore)-Number(b.awayScore):Number(b.awayScore)-Number(b.homeScore);
  const lines=split(b.line),parts=lines.map(x=>simple(margin+x)),outcome=combine(parts);
  return{market:'asian_handicap',outcome,...multipliers(outcome,b.odds),components:lines.map((line,i)=>({line,outcome:parts[i]}))};
}
function dnb(b){
  if(b.voided)return{market:'draw_no_bet',outcome:'void',...multipliers('void',b.odds),components:[{line:0,outcome:'void'}]};
  const margin=String(b.side)==='home'?Number(b.homeScore)-Number(b.awayScore):Number(b.awayScore)-Number(b.homeScore),outcome=simple(margin);
  return{market:'draw_no_bet',outcome,...multipliers(outcome,b.odds),components:[{line:0,outcome}]};
}
function european(b){
  if(b.voided)return{market:'european_handicap',outcome:'void',...multipliers('void',b.odds),components:[{line:Number(b.homeHandicap),outcome:'void'}]};
  const adjusted=Number(b.homeScore)+Number(b.homeHandicap),away=Number(b.awayScore);
  const result=adjusted>away?'home':adjusted<away?'away':'draw';
  const outcome=String(b.selection)===result?'win':'loss';
  return{market:'european_handicap',outcome,...multipliers(outcome,b.odds),components:[{line:Number(b.homeHandicap),outcome}]};
}
export default function handler(req,res){
  if(req.method==='OPTIONS'){res.setHeader('Access-Control-Allow-Origin',req.headers.origin||'*');res.setHeader('Access-Control-Allow-Methods','POST,OPTIONS');res.setHeader('Access-Control-Allow-Headers','Content-Type');return res.status(204).end()}
  if(req.method!=='POST')return send(res,405,{error:'Método no permitido'});
  try{
    const b=req.body||{},market=String(b.market||'');
    if(!Number.isFinite(Number(b.homeScore))||!Number.isFinite(Number(b.awayScore)))return send(res,400,{error:'homeScore y awayScore son obligatorios'});
    let result;
    if(market==='asian_handicap'){
      if(!['home','away'].includes(String(b.side))||!Number.isFinite(Number(b.line)))return send(res,400,{error:'Asian handicap requiere side y line'});
      result=asian(b);
    }else if(market==='draw_no_bet'){
      if(!['home','away'].includes(String(b.side)))return send(res,400,{error:'DNB requiere side'});
      result=dnb(b);
    }else if(market==='european_handicap'){
      if(!['home','draw','away'].includes(String(b.selection))||!Number.isFinite(Number(b.homeHandicap)))return send(res,400,{error:'European handicap requiere selection y homeHandicap'});
      result=european(b);
    }else return send(res,400,{error:'Mercado no soportado'});
    return send(res,200,{ok:true,result});
  }catch(e){return send(res,500,{error:e instanceof Error?e.message:String(e)})}
}
