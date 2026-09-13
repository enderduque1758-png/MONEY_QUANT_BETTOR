import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'football-insights'};return handler(req,res)}
