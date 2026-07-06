#!/usr/bin/env python3
"""
Standalone weather lookup CLI.
Resolves its own path so it works from any working directory.
Usage: python tools.py "London"
       python tools.py "New York"
       python tools.py "Tokyo, JP"
"""

import sys
import os

# Resolve to the skill directory so weather.py import works
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

# Import and delegate to weather.py
import weather  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools.py <location>")
        print("Examples:")
        print("  python tools.py London")
        print('  python tools.py "New York"')
        print('  python tools.py "München, DE"')
        sys.exit(1)

    loc = " ".join(sys.argv[1:])
    w = weather.get_weather(loc)
    print(f"Location: {w['location']}")
    print(f"Condition: {w['condition']}")
    print(f"Temperature: {w['temp_c']}°C / {w['temp_f']}°F")
    print(f"Feels like: {w['feels_like_c']}°C / {w['feels_like_f']}°F")
    print(f"Humidity: {w['humidity']}%")
    print(f"Wind: {w['wind_kph']} km/h {w['wind_dir']}")
    print(f"Visibility: {w['visibility_km']} km")
    print(f"UV Index: {w['uv_index']}")


if __name__ == "__main__":
    main()