import http from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
import handler from './handler.js';

const root = resolve(process.cwd());
const publicDir = join(root, 'dist');
const port = Number(process.env.PORT || 10000);
const host = '0.0.0.0';
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2'
};

function enhance(req, res) {
  res.req = req;
  res.status = code => { res.statusCode = code; return res; };
  res.json = data => {
    if (res.writableEnded) return;
    res.setHeader('content-type', 'application/json; charset=utf-8');
    res.setHeader('cache-control', 'no-store');
    res.end(JSON.stringify(data));
  };
}

async function parseBody(req) {
  if (!['POST', 'PUT', 'PATCH'].includes(req.method || 'GET')) return {};
  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (raw.length > 1024 * 1024) throw new Error('Solicitud demasiado grande');
  }
  if (!raw) return {};
  return JSON.parse(raw);
}

async function serveApi(req, res) {
  try {
    enhance(req, res);
    req.body = await parseBody(req);
    req.query = Object.fromEntries(new URL(req.url, 'http://local').searchParams);
    await handler(req, res);
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : 'Error interno' });
  }
}

function serveStatic(req, res) {
  let pathname = '/';
  try { pathname = decodeURIComponent(new URL(req.url, 'http://local').pathname); } catch {}
  const requested = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  let file = normalize(join(publicDir, requested));
  if (!file.startsWith(publicDir) || !existsSync(file) || statSync(file).isDirectory()) file = join(publicDir, 'index.html');
  if (!existsSync(file)) {
    res.statusCode = 503;
    res.setHeader('content-type', 'application/json; charset=utf-8');
    return res.end(JSON.stringify({ error: 'Build no disponible' }));
  }
  res.statusCode = 200;
  res.setHeader('content-type', types[extname(file).toLowerCase()] || 'application/octet-stream');
  res.setHeader('x-content-type-options', 'nosniff');
  res.setHeader('cache-control', /\\.(?:html|js|css)$/i.test(file) ? 'no-store, max-age=0' : 'public, max-age=3600');
  createReadStream(file).pipe(res);
}

const server = http.createServer((req, res) => {
  if ((req.url || '').startsWith('/api/')) return void serveApi(req, res);
  serveStatic(req, res);
});

server.listen(port, host, () => console.log(`Money Quant Bettor listo en ${host}:${port}`));
