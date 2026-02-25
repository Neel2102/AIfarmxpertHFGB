import requests
import json
from datetime import datetime

API_KEY = "2675dc82bdd9cf780ea9efe429a50129"

def check_nitrogen_status(value):
    if value < 140:
        return "low"
    elif value < 280:
        return "medium"
    else:
        return "high"

def get_rain_probability(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()

    rain_slots = 0
    for item in data.get("list", [])[:8]:
        if item.get("pop", 0) > 0.5:
            rain_slots += 1

    if rain_slots >= 5:
        return "high"
    elif rain_slots >= 3:
        return "medium"
    else:
        return "low"




HISTORY_FILE = "fertilizer_history.json"

def days_since_last_application(crop, fertilizer):
    try:
        with open(HISTORY_FILE) as f:
            data = json.load(f)
    except:
        return 999

    today = datetime.today()

    for entry in reversed(data):
        if entry["crop"] == crop and entry["fertilizer"] == fertilizer:
            last_date = datetime.strptime(entry["date"], "%Y-%m-%d")
            return (today - last_date).days

    return 999

def check_potassium_status(value):
    if value < 120:
        return "low"
    elif value < 280:
        return "medium"
    else:
        return "high"


def save_fertilizer_application(crop, fertilizer):
    from datetime import datetime
    import json

    try:
        with open(HISTORY_FILE) as f:
            data = json.load(f)
    except:
        data = []

    data.append({
        "crop": crop,
        "fertilizer": fertilizer,
        "date": datetime.today().strftime("%Y-%m-%d")
    })

    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_phosphorus_status(value):
    if value < 10:
        return "low"
    elif value < 25:
        return "medium"
    else:
        return "high"

    # rain_count = 0
    # for item in data["list"][:8]:   # next 24 hours
    #     if "rain" in item:
    #         rain_count += 1

    # if rain_count >= 3:
    #     return "high"
    # else:
    #     return "low"
