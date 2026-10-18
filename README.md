# India Civic Pulse

A map-first civic information reader connecting public-interest updates to source records, dates and carefully caveated geography.

## What works

- Responsive story feed with text search, topic filters and story details.
- Interactive Leaflet map with markers for source-text location matches.
- Scheduled ingestion of the Press Information Bureau (PIB) press-release RSS feed into a JSON snapshot.
- Publication timestamps, canonical source links, publisher attribution, retrieval metadata and feed-health status.
- Conservative geography: city mentions are caveated, state markers use approximate centroids, unmatched items remain national.
- Automated Python tests and GitHub Actions workflows for ingestion and GitHub Pages deployment.
- No API key or database is required for this first live-data slice.

## Run locally

Requires Python 3.10+ and internet access for the official RSS feed, map tiles and external fonts.

\`\`\`bash
python -m unittest discover -s tests -v
python scripts/ingest.py --output data/stories.json
python -m http.server 8000
\`\`\`

Open http://localhost:8000. Run ingestion before starting the server. Opening the page via file:// will not load the JSON dataset because browsers restrict local file fetches.

## Live-data scope and limitations

The first automated sources are the official [PIB Headquarters press-release RSS feed](https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1) and [PIB Delhi press-release RSS feed](https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3). It provides genuine source-linked records, but it is not a comprehensive feed of every Indian public institution. Items are publisher records, not independently fact-checked stories. Keyword-based categories and place mentions are discovery aids and may be wrong. No LLM is used to generate or embellish summaries.

The ingestion workflow runs every six hours and can be run manually from **Actions → Refresh civic data**. It writes data/stories.json and commits only when the snapshot changes. Feed failures are surfaced in workflow logs; the application does not silently substitute invented sample stories.

## Deployment

The repository is a static site and needs no build step. The Deploy GitHub Pages workflow publishes the repository root on pushes to main and after successful data refreshes. In GitHub repository Settings → Pages, select GitHub Actions as the build and deployment source if it is not already enabled. The first successful deployment publishes the site; the public URL appears in the workflow deployment environment. The ingestion workflow commits refreshed JSON snapshots to main, so the deployed site updates as the feed refreshes.

## Architecture

- scripts/ingest.py: RSS retrieval, parsing, normalization, category hints, cautious location matching and source status.
- data/stories.json: generated static API consumed by the frontend.
- app.js: filters, map, story details, freshness and error states.
- .github/workflows/update-data.yml: scheduled/manual ingestion.
- .github/workflows/pages.yml: static site deployment.
- tests/test_ingest.py: parser, date, category and location tests.

## Next production milestones

Add separately governed source adapters for parliamentary records, e-Gazette notifications, state government releases and local civic data; persist corrections and review decisions; add reviewed place entity resolution and source monitoring. Introduce a backend only if volume or editorial workflow requires it. Do not add AI summaries until claim-level citations and source text can be preserved.

## Editorial principles

- Original source links before summaries.
- Publication time and retrieval time are separate.
- A place mention is not proof of event location.
- Never fabricate records when a feed is unavailable.
- Keep publisher claims distinguishable from independent verification.
- Respect source terms, rate limits and content licensing.

Independent civic-information project; not affiliated with the Government of India, Parliament or any civic authority.
