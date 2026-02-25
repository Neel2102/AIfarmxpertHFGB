from farmxpert.agents.analytics.profit_agent.tool import (
    load_expenses,
    calculate_total_expense,
    get_crop_market_prices,
    calculate_revenue,
    calculate_profit,
    load_context,
    save_context
)

from datetime import datetime

def profit_optimization_agent(crop, area_acre, yield_per_acre):
    # ---------------- YIELD ----------------
    expected_yield = area_acre * yield_per_acre

    # ---------------- EXPENSE ----------------
    expenses = load_expenses()
    total_expense = calculate_total_expense(expenses)

    # ---------------- MARKET ----------------
    market_prices = get_crop_market_prices(crop)

    # Load existing context
    context = load_context()

    # -------- CASE 1: NO MARKET DATA --------
    if not market_prices:
        run_summary = {
            "timestamp": datetime.now().isoformat(),
            "crop": crop,
            "area_acre": area_acre,
            "yield_per_acre": yield_per_acre,
            "expected_yield": expected_yield,
            "total_expense": total_expense,
            "status": "no_market_data"
        }

        context["last_run"] = run_summary
        context["history"].append(run_summary)
        save_context(context)

        return {
            "status": "no_market_data",
            "crop": crop,
            "area_acre": area_acre,
            "yield_per_acre": yield_per_acre,
            "expected_yield": expected_yield,
            "expenses": expenses,
            "total_expense": total_expense
        }

    # -------- CASE 2: MARKET DATA AVAILABLE --------
    market_table = []

    for market, price in market_prices.items():
        revenue = calculate_revenue(expected_yield, price)
        profit = calculate_profit(revenue, total_expense)

        market_table.append({
            "market": market,
            "price": price,
            "revenue": revenue,
            "profit": profit
        })

    best_market = max(market_table, key=lambda x: x["price"])

    # -------- SAVE CONTEXT --------
    run_summary = {
        "timestamp": datetime.now().isoformat(),
        "crop": crop,
        "area_acre": area_acre,
        "yield_per_acre": yield_per_acre,
        "expected_yield": expected_yield,
        "total_expense": total_expense,
        "best_market": best_market["market"],
        "best_price": best_market["price"],
        "best_profit": best_market["profit"],
        "status": "success"
    }

    context["last_run"] = run_summary
    context["history"].append(run_summary)
    save_context(context)

    return {
        "status": "success",
        "crop": crop,
        "area_acre": area_acre,
        "yield_per_acre": yield_per_acre,
        "expected_yield": expected_yield,
        "expenses": expenses,
        "total_expense": total_expense,
        "market_comparison_table": market_table,
        "best_market": best_market
    }
