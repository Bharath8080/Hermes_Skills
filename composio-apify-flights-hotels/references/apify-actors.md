# Apify Actors for Travel Search (via Composio)

## Flight Scraper (Primary)

**Actor:** `makework36/flight-price-scraper` — 63K+ runs, white-listed

**Input schema:**
```json
{
  "origin": "VTZ",              // Required — IATA code
  "destination": "COK",         // Required — IATA code
  "departDate": "2026-07-15",   // Required — YYYY-MM-DD
  "returnDate": "2026-07-22",   // Optional — YYYY-MM-DD for round trip
  "adults": 2,                  // Optional — default 1, max 9
  "cabinClass": "ECONOMY",      // Optional — ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
  "currency": "INR",            // Optional — default USD
  "maxFlights": 50              // Optional — default 50, max 200
}
```

**Output:** Structured JSON per flight with:
- `airline`, `bestPrice`, `currency`, `stops`
- `departTime`, `arriveTime`, `duration`
- `segments[]` — per-leg: flightCode, departure/arrival times, duration, from/to airports
- `layovers[]` — airport, city, duration
- `prices{google, kiwi}` — per-source price comparison
- `links{book, googleFlights, kiwi}` — booking URLs
- `baggage` — included checked/hand bags
- `highlights{isCheapest, isFastest, isBest}`

**Cost:** $0.00005/start + $0.0025/result. ~$0.13 for 50 results.

**Usage via Composio:**
```python
APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS(
  actorId="makework36~flight-price-scraper",
  input={...},
  maxItems=50,
  waitForFinish=120
)
```

**Notes:**
- No `children` or `infants` param in input schema
- No `direct` filter — filter results client-side by `stops === 0`
- Returns round-trip total price when `returnDate` is set
- Sources: Google Flights + Kiwi.com (prices compared per flight)

---

## Hotel Scrapers (Available)

| Actor | ID | Runs | WL | Notes |
|-------|-----|:----:|:--:|-------|
| Booking.com Scraper | `automation-lab/booking-scraper` | 3,725 | ✅ | Most popular. Prices, ratings, reviews. |
| Fast Booking Scraper | `makework36/fast-booking-scraper` | 165 | ✅ | Same author as flight scraper. |
| Booking+Kayak Aggregator | `apage/travel-price-aggregator` | 213 | ✅ | Compares both in one scrape, deduplicates. |
| VRBO + Expedia | `makework36/vrbo-scraper` | 771 | ✅ | Vacation rentals + Expedia hotels. |
| Trivago Aggregator | `buseta/trivago-scraper` | 191 | ✅ | Aggregates Booking, Hotels.com, Expedia. |
| Google Hotels Multi | `jy-labs/google-hotels-multi-query-scraper` | 599 | ❌ | 30+ OTAs compared, not white-listed. |

**Preferred pick:** `automation-lab/booking-scraper` (most runs) or `apage/travel-price-aggregator` (multi-source).