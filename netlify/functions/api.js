import genericHandler from '../../api/[...path].js';
import healthHandler from '../../api/health.js';
import preflightHandler from '../../api/preflight.js';
import stateHandler from '../../api/state.js';
import settleHandler from '../../api/settle.js';
import closingLineHandler from '../../api/closing-line.js';
import sportsHandler from '../../api/sports.js';
import oddsHandler from '../../api/odds.js';
import footballInsightsHandler from '../../api/football-insights.js';
import marketIntelHandler from '../../api/market-intel.js';
import modelHistoryHandler from '../../api/model-history.js';

const handlers = {
  health: healthHandler,
  preflight: preflightHandler,
  state: stateHandler,
  settle: settleHandler,
  'closing-line': closingLineHandler,
  sports: sportsHandler,
  odds: oddsHandler,
  'football-insights': footballInsightsHandler,
  'market-intel': marketIntelHandler,
  'model-history': modelHistoryHandler,
};

function makeReq(request) {
  const url = new URL(request.url);
  const headers = {};
  for (const [k, v] of request.headers.entries()) headers[k.toLowerCase()] = v;
  const query = {};
  for (const [k, v] of url.searchParams.entries()) {
    if (Object.prototype.hasOwnProperty.call(query, k)) {
      query[k] = Array.isArray(query[k]) ? [...query[k], v] : [query[k], v];
    } else query[k] = v;
  }
  const path = url.pathname.replace(/^\/api\/?/, '').replace(/^\/+|\/+$/g, '');
  query.path = path;
  return { method: request.method, url: url.pathname + url.search, headers, query, body: {} };
}

function makeRes(req) {
  const headers = new Headers();
  let statusCode = 200;
  let payload = '';
  const res = {
    req,
    setHeader(name, value) { headers.set(name, Array.isArray(value) ? value.join(', ') : String(value)); return res; },
    status(code) { statusCode = Number(code) || 200; return res; },
    json(data) { if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json; charset=utf-8'); payload = JSON.stringify(data ?? null); return res; },
    end(data = '') { payload = data == null ? '' : String(data); return res; },
    get statusCode() { return statusCode; },
    get payload() { return payload; },
    get headers() { return headers; },
  };
  return res;
}

async function parseBody(request, req) {
  if (request.method === 'GET' || request.method === 'HEAD') return;
  const type = request.headers.get('content-type') || '';
  if (type.includes('application/json')) {
    try { req.body = await request.json(); } catch { req.body = {}; }
  } else {
    try { const text = await request.text(); req.body = text ? { raw: text } : {}; } catch { req.body = {}; }
  }
}

export default async (request) => {
  const req = makeReq(request);
  await parseBody(request, req);
  const res = makeRes(req);
  const route = String(req.query.path || '').split('/')[0];
  const handler = handlers[route] || genericHandler;
  try { await handler(req, res); }
  catch (error) { res.status(500).json({ error: error instanceof Error ? error.message : String(error) }); }
  return new Response(res.payload, { status: res.statusCode, headers: res.headers });
};

export const config = { path: '/api/*' };
