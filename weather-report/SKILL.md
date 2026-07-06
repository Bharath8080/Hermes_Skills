---
name: weather-report
description: Get current weather conditions for any city/location worldwide using wttr.in (free, no API key). Run: python C:/Users/homeu/AppData/Local/hermes/skills/research/weather-report/scripts/tools.py "London"
category: research
priority: 100
triggers_regex:
  - ".*weather.*"
  - ".*current.*(?:temp|condition|forecast).*"
  - "what.*(?:is|'s).*weather.*"
scripts:
  - scripts/weather.py
  - scripts/tools.py
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

```bash
# tools.py wrapper (preferred — resolves its own path from any cwd):
python C:/Users/homeu/AppData/Local/hermes/skills/research/weather-report/scripts/tools.py "London"

# Direct:
python C:/Users/homeu/AppData/Local/hermes/skills/research/weather-report/scripts/weather.py "London"

# Via curl (fastest, no Python):
curl "wttr.in/London?format=j1" | jq '.current_condition[0]'
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

## Windows Path Quirk (CRITICAL)

From git-bash, **do NOT use** `/c/Users/...` prefix with Windows `python.exe` — it causes a double `C:\c\` prefix error.

**WRONG** (double prefix):
```
python /c/Users/homeu/.../tools.py "London"  # → C:\c\Users\homeu\... (fails)
```

**RIGHT** (use forward slashes with drive letter):
```
python C:/Users/homeu/.../tools.py "London"   # works
```

The Hermes agent knows the correct path from skill metadata — just use the absolute path with `C:/` prefix.

## Prerequisites

- Python 3 (stdlib only — urllib, json, sys — no pip install needed)
- Internet connection

## Pitfalls

- **City disambiguation**: If a city name exists in multiple countries, use `"City, Country"` format — e.g. `"London, UK"` vs `"London, Canada"`.
- **Non-English characters**: UTF-8 city names (München, São Paulo) work fine — urllib.quote handles encoding.
- **No API key needed**: Unlike OpenWeatherMap or WeatherAPI, wttr.in is completely free and open-source.
- **Rate limits**: Very generous (public service). For programmatic bulk queries, consider self-hosting wttr.in or using an API keyed service.
- **Data freshness**: Typically updates every 30-60 minutes from METAR stations — not hyper-realtime.