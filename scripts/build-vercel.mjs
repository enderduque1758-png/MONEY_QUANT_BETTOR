import { rm, mkdir, cp, copyFile } from 'node:fs/promises';

await rm('public',{recursive:true,force:true});
await mkdir('public',{recursive:true});
await copyFile('index.html','public/index.html');
await cp('src','public/src',{recursive:true});
console.log('Money Quant Bettor · Vercel static build ready');
