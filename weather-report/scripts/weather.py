import json, sys, urllib.request

BASE = "https://wttr.in"

def get_weather(location: str) -> dict:
    url = f"{BASE}/{urllib.request.quote(location)}?format=j1"
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.loads(r.read())
    cc = data["current_condition"][0]
    return {
        "location": f"{data['nearest_area'][0]['areaName'][0]['value']}, {data['nearest_area'][0]['country'][0]['value']}",
        "temp_c": cc["temp_C"],
        "temp_f": cc["temp_F"],
        "condition": cc["weatherDesc"][0]["value"],
        "humidity": cc["humidity"],
        "wind_kph": cc["windspeedKmph"],
        "wind_dir": cc["winddir16Point"],
        "feels_like_c": cc["FeelsLikeC"],
        "feels_like_f": cc["FeelsLikeF"],
        "visibility_km": cc["visibility"],
        "uv_index": cc["uvIndex"],
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python weather.py <location>")
        print("Examples: python weather.py London")
        print("          python weather.py New York")
        print("          python weather.py Tokyo")
        sys.exit(1)
    loc = " ".join(sys.argv[1:])
    w = get_weather(loc)
    print(f"Location: {w['location']}")
    print(f"Condition: {w['condition']}")
    print(f"Temperature: {w['temp_c']}°C / {w['temp_f']}°F")
    print(f"Feels like: {w['feels_like_c']}°C / {w['feels_like_f']}°F")
    print(f"Humidity: {w['humidity']}%")
    print(f"Wind: {w['wind_kph']} km/h {w['wind_dir']}")
    print(f"Visibility: {w['visibility_km']} km")
    print(f"UV Index: {w['uv_index']}")