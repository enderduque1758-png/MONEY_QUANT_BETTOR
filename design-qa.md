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

final result: passed
