import handler from './[...path].js';
export default function(req,res){req.query={...(req.query||{}),path:'health'};return handler(req,res)}
