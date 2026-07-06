---
name: weather-report
description: Get current weather conditions for any city/location worldwide using wttr.in (free, no API key). Run the script directly like stock-price — python scripts/weather.py "London" for clean formatted output.
category: research
priority: 100
triggers_regex:
  - ".*weather.*"
  - ".*current.*(?:temp|condition|forecast).*"
  - "what.*(?:is|'s).*weather.*"
scripts:
  - scripts/weather.py
metadata:
  hermes:
    tags: [weather, forecast, wttr]
    config:
      - key: weather_report.enabled
        description: "Enable weather lookup"
        default: true
        prompt: "Enable weather skill?"
      - key: weather_report.description
        description: "Display label for the skill"
        default: "Weather lookup via wttr.in"
        prompt: "Short description for the skill"
---

# Weather Report

Fetches current weather for any city using wttr.in — free, no API key, no signup.

## Usage

Run the script directly with a location:

```bash
python skills/weather-report/scripts/weather.py "London"
python skills/weather-report/scripts/weather.py "New York"
python skills/weather-report/scripts/weather.py "Tokyo"
```

Output:
```
Location: London, United Kingdom
Condition: Partly cloudy
Temperature: 15°C / 59°F
Feels like: 14°C / 57°F
Humidity: 72%
Wind: 19 km/h WSW
Visibility: 10 km
UV Index: 5
```

Or via curl (even faster, no Python needed):
```bash
curl "wttr.in/London?format=j1" | jq '.current_condition[0]'
```

## Prerequisites

- Python 3 (stdlib only — urllib, json, sys — no pip install needed)
- Internet connection

## Pitfalls

- **City disambiguation**: If a city name exists in multiple countries, use `"City, Country"` format — e.g. `"London, UK"` vs `"London, Canada"`.
- **Non-English characters**: UTF-8 city names (München, São Paulo) work fine — urllib.quote handles encoding.
- **No API key needed**: Unlike OpenWeatherMap or WeatherAPI, wttr.in is completely free and open-source.
- **Rate limits**: Very generous (public service). For programmatic bulk queries, consider self-hosting wttr.in or using an API keyed service.
- **Data freshness**: Typically updates every 30-60 minutes from METAR stations — not hyper-realtime.