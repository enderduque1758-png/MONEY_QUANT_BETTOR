import { rm, mkdir, copyFile, cp, readFile, writeFile } from 'node:fs/promises';

const dist = new URL('../dist/', import.meta.url);
const root = new URL('../', import.meta.url);

await rm(dist, { recursive: true, force: true });
await mkdir(new URL('./src/', dist), { recursive: true });

await copyFile(new URL('index.html', root), new URL('index.html', dist));
await cp(new URL('src/', root), new URL('src/', dist), { recursive: true });

const mainPath = new URL('src/main.js', dist);
let main = await readFile(mainPath, 'utf8');
main = main.replace(/^\s*import\s+['"]\.\/styles\.css['"];?\s*/m, '');
await writeFile(mainPath, main, 'utf8');

console.log('Static build ready: dist/index.html + dist/src/*');
