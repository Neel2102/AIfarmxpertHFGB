from agent import profit_optimization_agent

print("\n========== FARMXPERT PROFIT OPTIMIZATION ==========\n")

crop = input("Enter crop name: ")
area_acre = float(input("Enter area (acre): "))
yield_per_acre = float(input("Enter yield per acre (quintal): "))

result = profit_optimization_agent(crop, area_acre, yield_per_acre)

print("\n================ PROFIT OPTIMIZATION REPORT =================\n")

# ---------------- YIELD DETAILS ----------------
print("📌 YIELD DETAILS")
print("-" * 65)
print(f"{'Parameter':<40} {'Value':>20}")
print("-" * 65)
print(f"{'Crop':<40} {result['crop']:>20}")
print(f"{'Area (Acre)':<40} {result['area_acre']:>20}")
print(f"{'Yield per Acre (Qt)':<40} {result['yield_per_acre']:>20}")
print(f"{'Total Expected Yield (Qt)':<40} {result['expected_yield']:>20}")
print("-" * 65)

# ---------------- EXPENSE DETAILS ----------------
print("\n📌 EXPENSE DETAILS")
print("-" * 65)
print(f"{'Expense Type':<40} {'Cost (₹)':>20}")
print("-" * 65)

for expense, cost in result["expenses"].items():
    print(f"{expense:<40} {cost:>20}")

print("-" * 65)
print(f"{'TOTAL EXPENSE':<40} {result['total_expense']:>20}")
print("-" * 65)

# ---------------- MARKET PRICE COMPARISON ----------------
if result.get("status") != "success":
    print("\n⚠️ MARKET PRICE COMPARISON")
    print("-" * 65)
    print("No real-time market price data available today.")
    print("Market comparison and best market selection skipped.")
    print("-" * 65)
    print("\nℹ️ You can still use yield and expense analysis above.")
    exit()

# ---------------- MARKET TABLE ----------------
print("\n📌 MARKET PRICE COMPARISON")
print("-" * 95)
print(f"{'Market':<30} {'Price (₹/Qt)':>15} {'Revenue (₹)':>20} {'Profit (₹)':>20}")
print("-" * 95)

for row in result["market_comparison_table"]:
    print(
        f"{row['market']:<30} "
        f"{row['price']:>15.1f} "
        f"{row['revenue']:>20.1f} "
        f"{row['profit']:>20.1f}"
    )

print("-" * 95)

# ---------------- BEST MARKET ----------------
best = result["best_market"]

print("\n✅ BEST MARKET TO SELL")
print("-" * 55)
print(f"Market Name   : {best['market']}")
print(f"Selling Price: ₹{best['price']} per quintal")
print(f"Total Profit : ₹{best['profit']}")
print("-" * 55)
