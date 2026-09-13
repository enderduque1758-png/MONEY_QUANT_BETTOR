import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'market-intel'};return handler(req,res)}
