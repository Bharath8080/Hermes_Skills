---
name: composio-apify-flights-hotels
description: Flight & Hotel search via Composio Search (preferred) or Apify actors (Composio MCP) + Skyscanner/MMT/Kayak URL builders
version: 1.0
author: Bharath Munakala
license: MIT
platform: ["linux", "darwin", "windows"]
scripts:
  - scripts/travel_search.py
references:
  - references/apify-actors.md
---

# Travel Search — Apify via Composio

## When to Use
- User asks for flights, hotels, travel searches
- Need actual structured flight/hotel data (prices, times, ratings)
- Travel planning queries

## Architecture

Two paths:

```
Path A (Preferred): User → Agent → COMPOSIO_SEARCH_FLIGHTS (Composio Search toolkit) → Structured JSON
                                               (no auth needed, ~4s response)

Path B (Fallback):  User → Agent → Composio MCP → Apify Actor → Structured JSON
                                            (authenticated via connected Apify account)
```

## Quick Start

### Flights — Path A (Composio Search, preferred)
```bash
# Search via COMPOSIO_SEARCH_FLIGHTS tool — no Apify actor needed
# Use COMPOSIO_SEARCH_TOOLS first with { use_case: "search flights", known_fields: "..." }
# Then COMPOSIO_MULTI_EXECUTE_TOOL with arguments:
#   { departure_id: "BOM", arrival_id: "DEL", outbound_date: "2026-07-06", currency: "INR", adults: 1 }
```

### Flights — Path B (Apify Actor)
```bash
# 1. Generate Apify input JSON
python scripts/travel_search.py apify flights VTZ COK 2026-07-15 2026-07-22 --adults 2

# 2. Ask the agent:
#    "Run Apify flight scrape for VTZ → COK 2026-07-15 → 2026-07-22"
```

### Hotels
```bash
# 1. Generate Apify input JSON
python scripts/travel_search.py apify hotels Kochi 2026-07-15 2026-07-22 --adults 2

# 2. Ask the agent:
#    "Run Apify hotel scrape for Kochi 2026-07-15 → 2026-07-22"
```

### URL Builder (no API needed — open in browser)
```bash
python scripts/travel_search.py url skyscanner VTZ COK 260715 260722 --adults 2 --children 8
python scripts/travel_search.py url makemytrip VTZ COK 15/07/2026 22/07/2026 --adults 2
python scripts/travel_search.py url kayak VTZ COK 2026-07-15 2026-07-22 --direct
```

## Apify Actors

| Service | Actor ID | Runs | Pricing | Data Returned |
|---------|----------|:----:|:-------|---------------|
| **Flights** | `makework36~flight-price-scraper` | 63K | $0.00005 + $0.0025/result | airline, flight#, times, duration, stops, prices, booking links, baggage |
| **Hotels** | `makework36~fast-booking-scraper` | 165 | $0.00005 + $0.0015/result | name, address, price, rating, reviews, distance, room info, cancellation, Booking.com link |

### Flight Input
| Parameter | Required | Format | Example |
|-----------|:--------:|--------|---------|
| `origin` | ✅ | IATA code | VTZ |
| `destination` | ✅ | IATA code | COK |
| `departDate` | ✅ | YYYY-MM-DD | 2026-07-15 |
| `returnDate` | ❌ | YYYY-MM-DD | 2026-07-22 |
| `adults` | ❌ | int (1-9) | 2 |
| `cabinClass` | ❌ | ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST | ECONOMY |
| `currency` | ❌ | code | INR |
| `maxFlights` | ❌ | int (1-200) | 50 |

### Hotel Input
| Parameter | Required | Format | Example |
|-----------|:--------:|--------|---------|
| `destinations` | ✅ | [string] | ["Kochi"] |
| `checkin` | ✅ | YYYY-MM-DD | 2026-07-15 |
| `checkout` | ✅ | YYYY-MM-DD | 2026-07-22 |
| `adults` | ❌ | int (1-30) | 2 |
| `currency` | ❌ | code | INR |
| `maxResults` | ❌ | int (1-1000) | 10 |

## URL Builder Parameters (Skyscanner)

| Parameter | Format | Example | Notes |
|-----------|--------|---------|-------|
| origin | IATA code | VTZ | Departure airport |
| destination | IATA code | COK | Arrival airport |
| outboundDate | YYYYMMDD | 260715 | Departure date |
| inboundDate | YYYYMMDD | 260722 | Return date (omit for one-way) |
| adultsv2 | number | 2 | Adults (18+) |
| childrenv2 | pipe-separated ages | 8 | Child ages (2-17) |
| cabinclass | economy, premium_economy, business, first | economy | Cabin class |
| preferdirects | true/false | false | Only direct flights |
| sort | best, cheapest, fastest | cheapest | Sort results |
| currency | ISO code | INR | Currency |

## Composio Search (Alternative — No Apify needed)

The `COMPOSIO_SEARCH_FLIGHTS` tool (from `composio_search` toolkit, no auth required) returns live pricing, schedules, airlines, and booking links in ~4s — faster than Apify actors.

### COMPOSIO_SEARCH_FLIGHTS Input Parameters

| Parameter | Required | Format | Example |
|-----------|:--------:|--------|---------|
| `departure_id` | ✅ | IATA code | BOM |
| `arrival_id` | ✅ | IATA code | DEL |
| `outbound_date` | ✅ | YYYY-MM-DD | 2026-07-06 |
| `return_date` | ❌ | YYYY-MM-DD | 2026-07-10 |
| `adults` | ❌ | int | 1 |
| `children` | ❌ | int | 0 |
| `infants` | ❌ | int | 0 |
| `travel_class` | ❌ | 1-4 | 1 (Economy) |
| `currency` | ❌ | code | INR |
| `query` | ❌ | string | "Mumbai to Delhi" |
| `gl` | ❌ | country code | us |
| `hl` | ❌ | language code | en |

### Response Structure

```
best_flights[] — top recommendations
  └─ flights[] → airline, flight_number, departure_airport, arrival_airport, duration, airplane
  └─ price (INR)
  └─ total_duration (minutes)
  └─ type: "One way"

other_flights[] — additional options (same structure)
```

## Fallback: Tavily Search

If both Composio Search and Apify are unavailable, Tavily Search on partner sites returns price trends and schedule data.

Partner sites: makemytrip.com, cleartrip.com, easemytrip.com, goindigo.in, airindia.com, ixigo.com, kayak.co.in

## Agent Workflow

1. **Prefer Path A**: Search tools via `COMPOSIO_SEARCH_TOOLS` → execute `COMPOSIO_MULTI_EXECUTE_TOOL` with `COMPOSIO_SEARCH_FLIGHTS` — fastest path, ~4s response
2. **Fallback Path B**: Generate input JSON via `travel_search.py` → call Apify actor via `COMPOSIO_MULTI_EXECUTE_TOOL` (5-30s)
3. **Format**: Table with price, airline, flight#, times, duration

## Pitfalls
- **Path A preferred**: COMPOSIO_SEARCH_FLIGHTS (Google Flights via SerpAPI) is faster, cheaper, and auth-free — always try it first before Apify actors
- No direct Apify API token in env — scrapes run through agent via Composio MCP
- Flight scraper has no children param — use adult count only
- Actors need 5-30s to complete (browser rendering)
- For budget quick-look, use Tavily Search fallback