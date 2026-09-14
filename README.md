# MONEY QUANT BETTOR

Panel deportivo cuantitativo con cuotas, mercados, props de jugadores, combinadas, calibración, gestión de riesgo y funciones serverless para The Odds API y API-FOOTBALL.

## Versión simplificada

La interfaz compacta conserva todos los módulos importantes del motor pero reduce la densidad visual: filtros flotantes contraíbles, panel cuantitativo desplegable, navegación compacta, tarjetas de partidos más pequeñas y vistas de combinadas/mercados sin eliminar funcionalidad.

## Desarrollo local

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

El resultado se genera en `dist/`.

## Variables de entorno para Vercel

Configura en **Project Settings → Environment Variables**:

- `THE_ODDS_API_KEY`
- `API_FOOTBALL_KEY`

Nunca publiques las claves en GitHub. El frontend puede enviar una clave de The Odds API guardada localmente, pero para producción es preferible mantener las credenciales del servidor en Vercel.

## Vercel

El repositorio incluye `vercel.json`. Importa este repositorio en Vercel, selecciona el framework Vite y deja que Vercel ejecute `npm run build`. Las funciones dentro de `api/` se despliegan como funciones serverless.

## GitHub Pages

El workflow `.github/workflows/pages.yml` compila Vite y publica únicamente `dist/` cuando se actualiza `main`.

Cuando se usa GitHub Pages como frontend, las llamadas `/api` se redirigen desde el código del cliente al backend Vercel configurado para MONEY QUANT BETTOR.
