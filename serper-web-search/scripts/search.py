#!/usr/bin/env python3
"""
Serper API (google.serper.dev) CLI tool.

Usage:
  python search.py search "apple stock price" --gl in
  python search.py images "KL Rahul" --gl in --num 10
  python search.py news "IPL 2026" --gl in --page 2
  python search.py maps "restaurants" --location "Srikakulam" --gl in
  python search.py reviews "taj hotel" --gl in
  python search.py shopping "mechanical keyboard" --gl in --num 20
  python search.py videos "python tutorial" --gl in
  python search.py places "coffee shops" --gl in
  python search.py search "query" --gl in --num 10 --page 1

Environment:
  SERPER_API_KEY (required)

Output: JSON to stdout. Use jq to parse or pipe to a file.
"""

import os
import sys
import json
import argparse
import requests


API_BASE = os.environ.get("SERPER_API_BASE", "https://google.serper.dev")

ENDPOINTS = {
    "search":   {"path": "/search",   "desc": "Web search + knowledge graph"},
    "images":   {"path": "/images",   "desc": "Google Image search"},
    "news":     {"path": "/news",     "desc": "News articles with dates"},
    "maps":     {"path": "/maps",     "desc": "Maps, places, local business"},
    "reviews":  {"path": "/reviews",  "desc": "Business reviews & ratings"},
    "shopping": {"path": "/shopping", "desc": "E-commerce & product prices"},
    "videos":   {"path": "/videos",   "desc": "Video search results"},
    "places":   {"path": "/places",   "desc": "Local business info"},
}


def serper_search(endpoint: str, query: str, gl: str = "in",
                  page: int = 1, num: int = 10,
                  location: str = None) -> dict:
    """Call Serper API and return parsed JSON response."""
    url = f"{API_BASE}{endpoint}"

    payload = {
        "q": query,
        "gl": gl,
        "page": page,
        "num": num,
    }
    if location:
        payload["location"] = location
    if num:
        payload["num"] = num

    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("ERROR: SERPER_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_endpoints():
    """Print available endpoints and exit."""
    print("Serper API Endpoints (google.serper.dev)\n")
    print(f"{'Endpoint':<12} {'Usage'}")
    print("-" * 40)
    for name, info in ENDPOINTS.items():
        print(f"{name:<12} {info['desc']}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Serper API CLI — Search web, images, news, maps, reviews, shopping, videos, places",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("endpoint", nargs="?",
                        choices=list(ENDPOINTS.keys()) + ["help"],
                        help=f"Endpoint: {', '.join(ENDPOINTS.keys())}")
    parser.add_argument("query", nargs="?", default=None,
                        help="Search query (required for all endpoints except 'help')")
    parser.add_argument("--gl", default="in",
                        help="Country code (default: in)")
    parser.add_argument("--page", type=int, default=1,
                        help="Page number (default: 1)")
    parser.add_argument("--num", type=int, default=10,
                        help="Results per page (default: 10)")
    parser.add_argument("--location", default=None,
                        help="City/location for geo-specific search")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print JSON output")
    parser.add_argument("--list-endpoints", action="store_true",
                        help="List available endpoints and exit")

    args = parser.parse_args()

    if args.list_endpoints or args.endpoint == "help":
        list_endpoints()

    if not args.endpoint or not args.query:
        parser.print_help()
        sys.exit(1)

    endpoint_info = ENDPOINTS[args.endpoint]
    result = serper_search(
        endpoint=endpoint_info["path"],
        query=args.query,
        gl=args.gl,
        page=args.page,
        num=args.num,
        location=args.location,
    )

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))


if __name__ == "__main__":
    main()