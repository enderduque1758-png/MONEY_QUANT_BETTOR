import http from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
import engine from '../api/engine.js';

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

function json(res, status, value) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 'no-store');
  res.end(JSON.stringify(value));
}

async function bodyOf(req) {
  if (!['POST', 'PUT', 'PATCH'].includes(req.method || 'GET')) return undefined;
  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (raw.length > 1024 * 1024) throw new Error('Solicitud demasiado grande');
  }
  return raw || undefined;
}

async function serveApi(req, res) {
  try {
    const body = await bodyOf(req);
    const headers = new Headers();
    for (const [name, value] of Object.entries(req.headers)) {
      if (typeof value === 'string') headers.set(name, value);
    }
    const request = new Request('https://money-quant.local' + req.url, {
      method: req.method,
      headers,
      body
    });
    const response = await engine.fetch(request, {
      THE_ODDS_API_KEY: process.env.THE_ODDS_API_KEY || '',
      API_FOOTBALL_KEY: process.env.API_FOOTBALL_KEY || '',
      BETANO_SUPPORT_API_KEY: process.env.BETANO_SUPPORT_API_KEY || ''
    });
    res.statusCode = response.status;
    response.headers.forEach((value, name) => res.setHeader(name, value));
    res.setHeader('cache-control', 'no-store');
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) {
    json(res, 500, { error: error instanceof Error ? error.message : 'Error interno' });
  }
}

function serveStatic(req, res) {
  let pathname = '/';
  try { pathname = decodeURIComponent(new URL(req.url, 'http://local').pathname); } catch {}
  const requested = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  let file = normalize(join(publicDir, requested));
  if (!file.startsWith(publicDir) || !existsSync(file) || statSync(file).isDirectory()) file = join(publicDir, 'index.html');
  if (!existsSync(file)) return json(res, 503, { error: 'Build no disponible' });
  res.statusCode = 200;
  res.setHeader('content-type', types[extname(file).toLowerCase()] || 'application/octet-stream');
  res.setHeader('x-content-type-options', 'nosniff');
  createReadStream(file).pipe(res);
}

const server = http.createServer((req, res) => {
  if ((req.url || '').startsWith('/api/')) return void serveApi(req, res);
  serveStatic(req, res);
});

server.listen(port, host, () => console.log(`Money Quant Bettor listo en ${host}:${port}`));
