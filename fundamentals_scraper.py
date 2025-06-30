import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

def fetch_fundamentals(stock):
    url = f"https://www.screener.in/company/{stock}/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
    except:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    def get_metric(label):
        try:
            span = soup.find("span", string=re.compile(label, re.I))
            if span:
                return span.find_next("span").text.strip().replace('%', '').replace(',', '')
        except:
            return None
        return None

    return {
        "ROE": get_metric("ROE"),
        "P/E": get_metric("P/E"),
        "D/E": get_metric("Debt to equity"),
        "Promoter Holding": get_metric("Promoter holding"),
        "Valuation": get_metric("Valuation"),
        "Growth": get_metric("Growth"),
        "Red Flags": get_metric("Red Flags")
    }

# Load MACD candidates
df = pd.read_csv("potential_bullish_crossover.csv")

# Fetch fundamentals
enriched_data = []
for symbol in df["symbol"]:
    print(f"Fetching: {symbol}")
    data = fetch_fundamentals(symbol)
    if data:
        enriched_data.append({**{"symbol": symbol}, **data})
    time.sleep(1.5)  # to avoid Screener blocking you

# Merge and save
fund_df = pd.DataFrame(enriched_data)
final_df = df.merge(fund_df, on="symbol", how="left")
final_df.to_csv("enriched_bullish_signals.csv", index=False, encoding='utf-8-sig')
print("✅ Enriched file saved: enriched_bullish_signals.csv")
