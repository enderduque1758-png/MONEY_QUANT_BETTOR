import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'model-history'};return handler(req,res)}
