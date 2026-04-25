import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_coordinates(place: str) -> dict:
    try:
        response = requests.get(
            GEOCODING_URL,
            params={"name": place, "count": 1, "language": "ja"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results")
        if not results:
            return {"error": f"地点 '{place}' が見つかりませんでした。別の地点名を試してください。"}

        r = results[0]
        return {
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "name": r["name"],
            "country": r.get("country", ""),
        }
    except requests.RequestException as e:
        return {"error": f"ジオコーディングAPIエラー: {e}"}


def get_historical_weather(latitude: float, longitude: float, date: str) -> dict:
    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": date,
                "end_date": date,
                "hourly": "temperature_2m,relative_humidity_2m",
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return {"error": data.get("reason", "天気APIエラー")}

        hourly = data.get("hourly", {})
        temperatures = [t for t in hourly.get("temperature_2m", []) if t is not None]
        humidities = [h for h in hourly.get("relative_humidity_2m", []) if h is not None]

        if not temperatures:
            return {
                "error": (
                    f"日付 '{date}' のデータが存在しません。"
                    "取得可能期間は1940-01-01から約5日前までです。"
                )
            }

        return {
            "date": date,
            "avg_temperature_celsius": round(sum(temperatures) / len(temperatures), 1),
            "min_temperature_celsius": round(min(temperatures), 1),
            "max_temperature_celsius": round(max(temperatures), 1),
            "avg_humidity_percent": (
                round(sum(humidities) / len(humidities), 1) if humidities else None
            ),
        }
    except requests.RequestException as e:
        return {"error": f"天気APIエラー: {e}"}
