# Data sources, provenance and editorial policy

## Live adapters currently implemented

**Reserve Bank of India — Press Releases RSS**

- Feed: https://rbi.org.in/pressreleases_rss.xml
- Publisher RSS directory: https://www.rbi.org.in/Scripts/rss.aspx

**Securities and Exchange Board of India — RSS**

- Feed: https://www.sebi.gov.in/sebirss.xml
- Publisher RSS directory: https://www.sebi.gov.in/rss.html
- Covers press releases, circulars, orders and rulings.

The PIB RSS endpoints were also attempted but returned HTTP 403 from GitHub-hosted runners. They are not active adapters until a permitted retrieval path can be used.

For active adapters, stored fields include publisher-supplied title, description, direct URL, publication time and identifier; retrieval time; automated category; location-match metadata; and per-source health. Official records are not independently fact-checked by this application.

## Additional source registries for future adapters

These are discovery entry points, not sources attached to every current record:

- Digital Sansad: https://sansad.in/
- e-Gazette of India: https://egazette.gov.in/
- MyGov: https://www.mygov.in/
- Central Pollution Control Board: https://cpcb.nic.in/
- Municipal Corporation of Greater Mumbai: https://portal.mcgm.gov.in/

Each adapter must use a documented, permitted interface and preserve a direct link to the specific record. Portal homepages must never be represented as evidence for a story.

## Dataset contract

Each record in data/stories.json contains an ID, title, cleaned publisher summary, direct source URL, publisher attribution, publication time, retrieval time, automated category, location and confidence metadata, source type and verification caveat. The dataset envelope contains schemaVersion, generatedAt, storyCount, per-source health, stories and a notice.

## Geography safeguards

The ingestion script attaches city/state coordinates only when a place name appears in source text. These are approximate map centroids, not verified event coordinates. A place may be mentioned historically or comparatively; the frontend displays a caveat. When no known place appears, the record is marked as a national update at an approximate India centre point, not a precise event location. Future work should add reviewed entity resolution and never silently upgrade a text mention to a confirmed location.

## Reliability and content safeguards

- Feed requests have a timeout and response-size limit.
- Invalid items without a title, HTTPS source URL or publication date are skipped.
- Duplicate canonical URLs are removed.
- Feed failures are exposed in workflow logs; an all-source failure fails the workflow.
- Source text is HTML-cleaned and escaped before rendering.
- No AI summaries, unsupported claims or synthetic news items are generated.
- Respect publisher terms, rate limits and reuse conditions. The app links to original source pages rather than republishing full articles.

## Map tiles

The map uses OpenStreetMap tiles. Follow the tile usage policy: https://operations.osmfoundation.org/policies/tiles/. Production traffic may require a suitable tile provider.
