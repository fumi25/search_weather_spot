TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "地点名を緯度・経度に変換する。都市名、地名、国名などを受け付ける。",
            "parameters": {
                "type": "object",
                "properties": {
                    "place": {
                        "type": "string",
                        "description": "変換する地点名 (例: 東京, Paris, New York)",
                    }
                },
                "required": ["place"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_historical_weather",
            "description": "指定した緯度・経度と日付の過去の気温・湿度データを取得する。日付はYYYY-MM-DD形式のみ受け付ける。",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "緯度 (例: 35.6762)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "経度 (例: 139.6503)",
                    },
                    "date": {
                        "type": "string",
                        "description": "取得する日付 (YYYY-MM-DD形式, 例: 2023-07-15)",
                    },
                },
                "required": ["latitude", "longitude", "date"],
            },
        },
    },
]
