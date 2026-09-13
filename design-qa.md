# Design QA — Sportsbook Option 3

## Evidence

- Source visual truth: `/workspace/scratch/163eff1eccbf/generated_images/exec-8cc9225a-c420-40fb-a17c-7986abe2670c.png`.
- Browser-rendered implementation: cloud-browser capture from `https://money-quant-bettor-dve11oa92-duque3.vercel.app/?qa=option3`.
- Browser viewport: 1363 × 936 CSS px at device scale factor 1.
- Compared app region: 852 px wide; rendered page height 1506 px.
- Source image: 852 × 1854 px. Width was normalized 1:1; the source extends farther vertically because it includes more scrolled content.
- State: sportsbook feed with three representative events, one expanded confidence panel, 1-X-2 quotes, live/upcoming navigation, refresh status, and fixed AI bet-slip action.

## Full-view comparison

- Information hierarchy now follows the selected visual: MQ header → sport rail → freshness/credit strip → live/upcoming navigation → compact odds feed → quantitative pick explanation → AI bet-slip action.
- The previous landing-console hero, always-visible filter column, and large metrics stack no longer dominate the initial view.
- The near-black/navy surfaces, cyan information accents, lime active/positive states, thin blue borders, condensed display typography, and dense sportsbook spacing track the source direction.

## Focused comparison

- Header: logo, brand, live state, credits, API control, and the required “Consultar calendario” button are visible without obscuring the feed.
- Match card: league/time, both teams, three quote tiles, movement indicators, chevron, and “Más mercados” action are aligned to the source hierarchy.
- Expanded pick: confidence, edge, quarter-Kelly stake, confidence bar, and plain-language reason appear in a single bordered panel.
- Bottom action: “Combinada IA” and “Revisar” remain persistent, matching the source’s high-priority bet-slip treatment.

## Required fidelity surfaces

- Fonts and typography: Barlow Condensed handles the compact sportsbook display hierarchy; Inter handles controls and data. Weights, line height, truncation, and uppercase labels were checked after web fonts finished loading.
- Spacing and layout rhythm: 852 px comparison width, segmented navigation, compact event rows, 8–12 px control gaps, thin separators, and fixed bottom action match the source density.
- Colors and tokens: deep navy background, cyan status text, lime selection/value states, red live badge, muted blue-gray metadata, and high-contrast white data are consistently tokenized.
- Image and icon fidelity: Material Symbols provides the visible sports and action iconography. Team crests are intentionally omitted because the current live payload has no licensed crest source.
- Copy and content: labels match the product’s Spanish workflow and preserve the user’s calendar, API, markets, confidence, edge, Kelly, advanced-market, and combination terminology.

## Interaction checks

- “Consultar calendario” is visible and enabled.
- API settings opens and closes; stored credentials remain device-local and are not embedded in the deployment.
- Sport-family and live/upcoming controls update active state and filtering.
- “Más mercados”, analysis tabs, search, shuffle, collapsible risk panel, configuration drawer, and “Revisar” retain their existing handlers.
- Production build and JavaScript syntax pass.
- No application-origin console errors were observed. Browser-extension metadata errors were excluded because they are not emitted by Money Quant Bettor.

## Comparison history

- Earlier P1: production was a hybrid of the legacy console and option 3. Fixed by replacing the initial information architecture and event-card renderer.
- Earlier P2: the floating configuration drawer inherited a legacy `top` value and overlapped the header. Fixed with an explicit `top: auto`.
- Earlier P2: top opportunities could disappear when the stricter ticket selector returned no rows despite positive event candidates. Fixed with a positive-edge event fallback.

## Remaining polish

- P3: add licensed team crests if a reliable crest asset source is connected later.

## Current iteration

- The Top Opportunities component now renders up to 24 positive-edge rows, adds market-group filters, and exposes a working “VER TODAS” toggle. This iteration preserves the source palette, borders, typography, and responsive density.
- The market matrix now exposes one complete, selectable sport at a time and the event-market dialog is generated from that sport's catalog. The catalog uses documented The Odds API keys for soccer, basketball, tennis, baseball, ice hockey, and American football, with explicit automatic, per-event, and loaded states.
- Source issue capture: `/workspace/scratch/163eff1eccbf/upload/de0d41f3-f765-4afd-8f94-6010c1ea9f5d.png` (1448 × 122 px), showing the matrix header without usable per-sport navigation in the captured region.
- Browser-rendered implementation: `https://money-quant-bettor-duque3.vercel.app/?v=markets-v2`, captured at 1365 × 936 CSS px. The source is a focused header crop, so comparison was normalized by inspecting the corresponding matrix header plus the immediately following navigation and rows.
- Production interaction checks passed for all six tabs: Fútbol 27, Baloncesto 26, Tenis 9, Béisbol 20, Hockey 17, and Fútbol americano 20. Selecting Tenis displayed its nine sport-specific markets and preserved the automatic/per-event status legend.
- No application-origin console errors were observed; the only logged errors came from a browser extension. The local preview remained blocked by `net::ERR_BLOCKED_BY_CLIENT`, but production browser evidence and interaction testing completed successfully.

## Hidden-market button iteration

- Source visual truth: `/workspace/scratch/163eff1eccbf/upload/e86a8b27-3ac7-4310-bbda-b4666ae74f05.png` (1427 × 152 px).
- Browser-rendered implementation: `/workspace/scratch/163eff1eccbf/money-quant-bettor/implementation-market-buttons.png` (1148 × 195 px), captured from `https://money-quant-bettor-duque3.vercel.app/?v=hidden-markets-final` in cloud Chrome.
- Combined comparison: `/workspace/scratch/163eff1eccbf/money-quant-bettor/qa-market-buttons-comparison.png` (1148 × 317 px). The source was normalized to 1148 × 122 px; the implementation remained at native capture density.
- Viewport: 1365 × 936 CSS px, device scale factor 1. State: no API key in the verification browser, Córners selected, all market counters at zero.
- Full-view evidence: the implementation preserves the source's navy panel, lime star and active state, cyan borders, condensed title, compact subtitle, pill controls, counter badges, and horizontal toolbar rhythm. The additional buttons intentionally extend beyond the source crop and remain horizontally scrollable.
- Focused evidence: all eleven buttons are present: Todos, Ganador, Doble oportunidad, Totales, Hándicap, Ambos marcan, Periodos, Córners, Tarjetas, Jugadores, and Especiales. Zero-count buttons remain selectable and use a dashed inactive treatment. Selecting Córners changed `aria-pressed` to true and rendered its market-specific empty state.
- Fonts and typography: Barlow Condensed and Inter retain the source hierarchy, compact sizing, weight, line height, and truncation behavior.
- Spacing and layout rhythm: header padding, 8 px pill gaps, 32 px control height, section borders, and mobile-safe horizontal overflow match the established component.
- Colors and tokens: existing navy, cyan, lime, and muted blue-gray design tokens are reused; no new competing palette was introduced.
- Image and icon fidelity: no new raster assets were needed; the source uses the existing star mark and text controls.
- Copy and content: Spanish labels explicitly expose formerly hidden market families and explain an empty selection without implying that a market is unavailable permanently.
- Primary interactions tested: selecting the Córners zero-count button, active `aria-pressed` state, empty-state rendering, and horizontal overflow. No API call is triggered by these local filters.
- Console check: no application-origin warnings or errors were observed. Browser-extension metadata errors were excluded.
- Comparison history: initial browser capture did not render the component before data was loaded. Fixed by running the existing renderer during initialization and appending Top Opportunities to the zero-event state. The subsequent capture showed the complete toolbar and working selection state; no actionable P0/P1/P2 differences remain.

final result: passed
