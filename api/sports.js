import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'sports'};return handler(req,res)}
