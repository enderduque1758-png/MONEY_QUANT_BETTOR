# MONEY QUANT BETTOR · Vercel Import

## Import
- Repository: enderduque1758-png/MONEY_QUANT_BETTOR
- Framework Preset: Other
- Root Directory: ./
- Build Command: npm run build
- Output Directory: public
- Node.js: 22.x
- Production Branch: main

## Environment variables
Optional because the UI can send user-provided keys:
- THE_ODDS_API_KEY
- API_FOOTBALL_KEY

Optional integration flag:
- BETANO_SUPPORT_API_KEY

## Serverless routes
- GET /api/health
- GET /api/sports
- POST /api/odds
- POST /api/combo-odds
- POST /api/event-markets
- POST /api/event-odds
- POST /api/football-insights
- POST /api/model-history
- POST /api/market-intel
- POST /api/betano-support
- POST /api/settle-market

The frontend is built into public/. API files remain native Vercel Functions.
