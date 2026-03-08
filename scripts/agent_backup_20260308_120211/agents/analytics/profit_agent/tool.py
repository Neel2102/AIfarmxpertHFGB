from datetime import datetime
import json
import requests

# ---------------- LOAD EXPENSE DATA ----------------
def load_expenses():
    with open("expenses.json", "r") as file:
        return json.load(file)


def calculate_total_expense(expenses):
    return sum(expenses.values())


# ---------------- MARKET-WISE CROP PRICES ----------------
def get_crop_market_prices(crop):
    """
    Returns market-wise prices for a crop
    """
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    params = {
        "api-key": "579b464db66ec23bdd000001fb6fa730c92c4d1845022701986edadc",
        "format": "json",
        "limit": 300
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    market_prices = {}

    for record in data.get("records", []):
        commodity = str(record.get("commodity", "")).lower()
        market = record.get("market")
        modal_price = record.get("modal_price")

        if crop.lower() in commodity and market:
            try:
                price = float(modal_price)
                if price > 0:
                    market_prices[market] = price
            except:
                continue

    if not market_prices:
        print(f"⚠️ No market price data available today for {crop}")
        return {}

    return market_prices


# ---------------- CALCULATIONS ----------------
def calculate_revenue(yield_quintal, price):
    return yield_quintal * price


def calculate_profit(revenue, total_expense):
    return revenue - total_expense



# ---------------- CONTEXT MEMORY ----------------
def load_context():
    try:
        with open("context.json", "r") as file:
            return json.load(file)
    except:
        return {"last_run": {}, "history": []}


def save_context(context):
    with open("context.json", "w") as file:
        json.dump(context, file, indent=2)
