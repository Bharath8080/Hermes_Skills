#!/usr/bin/env python3
"""
Travel Search — Skyscanner URL Builder + Apify Scraper (via Agent)

Usage:
  # Build Skyscanner search URL (no API needed)
  python travel_search.py url VTZ COK 260715 260722 --adults 2 --children 8 --direct

  # Generate Apify input JSON for the agent to run
  python travel_search.py apify flights VTZ COK 260715 260722 --adults 2 --children 8
  python travel_search.py apify hotels "Kochi" 2026-07-15 2026-07-22 --adults 2

  # List available Apify actors
  python travel_search.py apify list
"""
import argparse, json
from urllib.parse import urlencode

# ══════════════════════════════════════════════════════════════════════════════
# APIFY ACTOR REFERENCE
# ══════════════════════════════════════════════════════════════════════════════

APIFY_ACTORS = {
    "flights": {
        "actorId": "makework36~flight-price-scraper",
        "title": "Skyscanner Flight Scraper API",
        "runs": 63190,
        "pricing": "$0.00005/start + $0.0025/result",
        "input_schema": {
            "origin": "IATA code (e.g. VTZ)",
            "destination": "IATA code (e.g. COK)",
            "departDate": "YYYY-MM-DD",
            "returnDate": "YYYY-MM-DD (optional, for round trip)",
            "adults": "int (1-9, default 1)",
            "cabinClass": "ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST",
            "currency": "USD | INR | EUR (default USD)",
            "maxFlights": "int (1-200, default 50)",
        },
    },
    "hotels": {
        "actorId": "makework36~fast-booking-scraper",
        "title": "Booking.com Scraper API - Hotels, Prices, Ratings & Rooms",
        "runs": 165,
        "pricing": "$0.00005/start + $0.0015/result",
        "input_schema": {
            "destinations": '["Kochi", "City name"]',
            "checkin": "YYYY-MM-DD",
            "checkout": "YYYY-MM-DD",
            "adults": "int (1-30, default 2)",
            "currency": "USD | INR | EUR (default USD)",
            "maxResults": "int (1-1000, default 25)",
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# SKYSCANNER URL BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_skyscanner_url(origin, destination, departure_date, return_date=None,
                         adults=1, children=None, cabin='economy', market='IN',
                         currency='INR', locale='en-IN', direct=False, sort='cheapest'):
    """Build a Skyscanner flight search URL.
    
    Date format: YYYYMMDD (e.g. 260715)
    Children: pipe-separated ages (e.g. '8' or '5|10')
    Sort: cheapest, best, fastest
    """
    base = "https://www.skyscanner.co.in/transport/flights"
    params = {
        'adultsv2': adults, 'cabinclass': cabin, 'market': market,
        'currency': currency, 'locale': locale,
        'rtn': 1 if return_date else 0,
        'preferdirects': 'true' if direct else 'false', 'sort': sort,
    }
    if children:
        params['childrenv2'] = str(children) if isinstance(children, int) else children
    path = f"{base}/{origin}/{destination}/{departure_date}/"
    if return_date:
        path += f"{return_date}/"
    return path + '?' + urlencode(params)


def build_makemytrip_url(origin, destination, departure_date, return_date=None,
                         adults=1, children=0, infants=0, cabin='E', trip_type='R'):
    """Build a MakeMyTrip flight search URL.
    
    Date format: DD/MM/YYYY (e.g. 15/07/2026)
    Cabin: E=Economy, B=Business, F=First, P=Premium Economy
    """
    cabin_map = {'economy': 'E', 'business': 'B', 'first': 'F', 'premium_economy': 'P'}
    cabin_code = cabin_map.get(cabin.lower(), 'E')
    itinerary = f"{origin}-{destination}-{departure_date}"
    if return_date:
        itinerary += f"_{destination}-{origin}-{return_date}"
    params = {
        'itinerary': itinerary, 'tripType': trip_type,
        'paxType': f"A-{adults}_C-{children}_I-{infants}",
        'intl': 'false', 'cabinClass': cabin_code, 'lang': 'eng',
    }
    return "https://www.makemytrip.com/flight/search?" + urlencode(params)


def build_kayak_url(origin, destination, departure_date, return_date=None,
                    sort='cheapest', direct=False):
    """Build a Kayak India flight search URL.
    
    Date format: YYYY-MM-DD (e.g. 2026-07-15)
    Sort: cheapest, best, fastest
    """
    sort_map = {'cheapest': 'price_a', 'best': 'bestflight_a', 'fastest': 'duration_a'}
    sort_code = sort_map.get(sort, 'price_a')
    path = f"https://www.kayak.co.in/flights/{origin}-{destination}/{departure_date}"
    if return_date:
        path += f"/{return_date}"
    params = {'sort': sort_code}
    if direct:
        params['fs'] = 'stops=0'
    return path + '?' + urlencode(params)


# ══════════════════════════════════════════════════════════════════════════════
# APIFY INPUT GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def generate_apify_flight_input(origin, destination, departure_date, return_date=None,
                                adults=1, children=0, cabin='ECONOMY', currency='INR',
                                max_flights=50):
    """Generate Apify flight scraper input JSON."""
    return {
        "actorId": "makework36~flight-price-scraper",
        "input": {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departDate": departure_date,
            "returnDate": return_date,
            "adults": adults,
            "cabinClass": cabin.upper(),
            "currency": currency,
            "maxFlights": max_flights,
        },
        "maxItems": max_flights,
        "waitForFinish": 120,
    }


def generate_apify_hotel_input(destination, checkin, checkout, adults=2,
                               currency='INR', max_results=10):
    """Generate Apify hotel scraper input JSON."""
    return {
        "actorId": "makework36~fast-booking-scraper",
        "input": {
            "destinations": [destination],
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "currency": currency,
            "maxResults": max_results,
        },
        "maxItems": max_results,
        "waitForFinish": 120,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description='Travel Search — URL Builder + Apify Scraper')
    sub = p.add_subparsers(dest='cmd', required=True)

    # ─── url (build Skyscanner/MMT/Kayak URLs) ──────────────────────────
    up = sub.add_parser('url', help='Build search URL (no API key needed)')
    up.add_argument('platform', choices=['skyscanner', 'makemytrip', 'kayak'], help='Platform')
    up.add_argument('origin', help='IATA code (e.g. VTZ, DEL)')
    up.add_argument('destination', help='IATA code (e.g. COK, BOM)')
    up.add_argument('departure', help='Date: YYYYMMDD (ss) DD/MM/YYYY (mmt) YYYY-MM-DD (kayak)')
    up.add_argument('return_date', nargs='?', default=None, help='Return date (same format)')
    up.add_argument('--adults', type=int, default=1)
    up.add_argument('--children', type=int, default=0, help='Children count (skyscanner)')
    up.add_argument('--infants', type=int, default=0, help='Infants (MMT only)')
    up.add_argument('--cabin', default='economy', choices=['economy', 'premium_economy', 'business', 'first'])
    up.add_argument('--direct', action='store_true', help='Direct flights only')
    up.add_argument('--sort', default='cheapest', choices=['cheapest', 'best', 'fastest'])

    # ─── apify (generate Apify input JSON) ──────────────────────────────
    ap = sub.add_parser('apify', help='Generate Apify scraper input for the agent')
    ap.add_argument('mode', choices=['flights', 'hotels', 'list'], help='Scrape mode or list actors')
    ap.add_argument('origin_or_dest', nargs='?', help='Origin IATA (flights) or destination city (hotels)')
    ap.add_argument('destination_or_checkin', nargs='?', help='Destination IATA (flights) or checkin date (hotels)')
    ap.add_argument('departure_or_checkout', nargs='?', help='Departure date (flights) or checkout date (hotels)')
    ap.add_argument('return_date', nargs='?', default=None, help='Return date (flights only)')
    ap.add_argument('--adults', type=int, default=2)
    ap.add_argument('--children', type=int, default=0, help='Children (flights only)')
    ap.add_argument('--cabin', default='ECONOMY', choices=['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'])
    ap.add_argument('--currency', default='INR', help='Currency code (INR, USD, EUR)')
    ap.add_argument('--max', type=int, default=10, help='Max results')

    args = p.parse_args()

    # ═══ URL BUILDER ══════════════════════════════════════════════════════
    if args.cmd == 'url':
        if args.platform == 'skyscanner':
            children_str = str(args.children) if args.children else None
            url = build_skyscanner_url(args.origin, args.destination, args.departure,
                                       args.return_date, adults=args.adults, children=children_str,
                                       cabin=args.cabin, direct=args.direct, sort=args.sort)
        elif args.platform == 'makemytrip':
            url = build_makemytrip_url(args.origin, args.destination, args.departure,
                                       args.return_date, adults=args.adults, children=args.children,
                                       infants=args.infants, cabin=args.cabin)
        elif args.platform == 'kayak':
            url = build_kayak_url(args.origin, args.destination, args.departure,
                                  args.return_date, sort=args.sort, direct=args.direct)
        print(url)
        return

    # ═══ APIFY ════════════════════════════════════════════════════════════
    if args.cmd == 'apify':
        if args.mode == 'list':
            print(f"\n{'='*70}")
            print("  Available Apify Actors (via Composio)")
            print(f"{'='*70}\n")
            for svc, info in APIFY_ACTORS.items():
                print(f"  [{svc.upper()}] {info['title']}")
                print(f"  Actor ID: {info['actorId']}")
                print(f"  Runs: {info['runs']:,}  |  Pricing: {info['pricing']}")
                print(f"  Input: {json.dumps(info['input_schema'], indent=4)}")
                print()
            print(f"  Usage: python travel_search.py apify flights <args>")
            print(f"         python travel_search.py apify hotels <args>")
            print()
            print("  Then ask the agent to run the scrape with the generated JSON.")
            return

        if args.mode == 'flights':
            if not all([args.origin_or_dest, args.destination_or_checkin, args.departure_or_checkout]):
                print("Usage: python travel_search.py apify flights VTZ COK 2026-07-15 2026-07-22 --adults 2")
                return
            inp = generate_apify_flight_input(
                args.origin_or_dest, args.destination_or_checkin,
                args.departure_or_checkout, args.return_date,
                adults=args.adults, children=args.children,
                cabin=args.cabin, currency=args.currency, max_flights=args.max,
            )
            print(json.dumps(inp, indent=2))
            print()
            label = f"{args.origin_or_dest.upper()} → {args.destination_or_checkin.upper()}"
            dates = f"{args.departure_or_checkout}"
            if args.return_date:
                dates += f" → {args.return_date}"
            print(f"  → Ask the agent: 'Run Apify flight scrape for {label} {dates}'")
            return

        if args.mode == 'hotels':
            if not all([args.origin_or_dest, args.destination_or_checkin, args.departure_or_checkout]):
                print("Usage: python travel_search.py apify hotels Kochi 2026-07-15 2026-07-22 --adults 2")
                return
            inp = generate_apify_hotel_input(
                args.origin_or_dest, args.destination_or_checkin,
                args.departure_or_checkout, adults=args.adults,
                currency=args.currency, max_results=args.max,
            )
            print(json.dumps(inp, indent=2))
            print()
            print(f"  → Ask the agent: 'Run Apify hotel scrape for {args.origin_or_dest} {args.destination_or_checkin} → {args.departure_or_checkout}'")
            return


if __name__ == '__main__':
    main()