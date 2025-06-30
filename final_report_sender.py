import pandas as pd
import requests

TELEGRAM_TOKEN = "YOUR TELEGRAM TOKEN"
CHAT_ID = "TELEGRAM CHAT ID"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def generate_comment(row):
    comments = []
    action = "✅ Consider for Entry"

    if row.get("volume_surge") == True:
        comments.append("🔸 Volume is increasing ✅")
    else:
        comments.append("🔻 No volume surge ❌")
        action = "⚠️ Watchlist Only – Weak volume"

    if row.get("above_ema200") == True:
        comments.append("🔸 Price is above 200 EMA ✅")
    else:
        comments.append("🔻 Price is below 200 EMA ❌")
        action = "⚠️ Watchlist Only – Trend not confirmed"

    try:
        gap = float(row.get("actual_diff", 0))
        closeness = float(row.get("closeness_score", 999))
        if abs(gap) <= 0.3 and -1 <= closeness <= 2:
            comments.append("🔸 MACD crossover happening ✅")
        elif closeness < -2 or gap < -0.3:
            comments.append("🔻 Too early – MACD not ready ❌")
            action = "🔻 Wait – Not ready"
        elif closeness > 3:
            comments.append("🔻 MACD already happened ❌ Late signal")
            action = "🚫 Avoid – Signal is outdated"
    except:
        comments.append("🔻 MACD data missing ❌")

    try:
        roe = float(row.get("ROE", 0))
        if roe < 13:
            comments.append("🔻 ROE below 13 ❌ (Low profitability)")
            if "✅" in action:
                action = "⚠️ Watchlist Only – Weak fundamentals"
        else:
            comments.append("🔸 ROE is strong ✅")
    except:
        comments.append("🔻 ROE not available ❌")

    comments.append(f"\n📝 Action: <b>{action}</b>")
    return "\n".join(comments), action

# Load data
df = pd.read_csv("enriched_bullish_signals.csv")

# Generate comments and actions
comment_texts = []
for idx, row in df.iterrows():
    comment, action = generate_comment(row)
    comment_texts.append(comment)

df["comments"] = comment_texts
df.to_csv("final_bullish_signals_with_comments.csv", index=False, encoding='utf-8-sig')
print("✅ Final file saved with comments.")

# Send only qualified alerts
for _, row in df.iterrows():
    if "✅ Consider for Entry" not in row["comments"]:
        continue
    message = f"<b>📈 Stock Alert: {row['symbol']}</b>\n\n{row['comments']}"
    send_to_telegram(message)

print("✅ Alerts sent to Telegram.")
