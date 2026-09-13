import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'odds'};return handler(req,res)}
