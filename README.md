# MONEY QUANT BETTOR

Sportsbook cuantitativo con cuotas, mercados avanzados, props de jugadores, combinadas, calibración, gestión de riesgo y funciones serverless para The Odds API y API-Football.

## Desarrollo local

```bash
npm install
npm run build
```

El build de Vercel genera el frontend estático en `public/`.

## Importación en Vercel

- Framework Preset: **Other**
- Root Directory: `./`
- Build Command: `npm run build`
- Output Directory: `public`
- Node.js: `22.x`
- Production Branch: `main`

Las rutas dentro de `api/` se despliegan como Vercel Functions.

## Variables de entorno

Configura en **Project Settings → Environment Variables**:

- `THE_ODDS_API_KEY`
- `API_FOOTBALL_KEY`
- `BETANO_SUPPORT_API_KEY` (opcional)

El frontend también puede enviar temporalmente las claves de The Odds API y API-Football desde la sesión del navegador.

## Nota

La antigua versión Streamlit fue retirada del repositorio para evitar que Vercel detecte `app.py` como runtime Python.
