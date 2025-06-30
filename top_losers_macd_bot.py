# top_losers_macd_bot.py (Enhanced for Batch Processing, Logging & Validation)

import pandas as pd
import time
from smart_login import get_smartapi_client
from utils import get_stock_data, send_telegram_message, log_alert
from indicators_correct import add_technical_indicators, get_engulfing_alerts

def get_top_losers(top_n=300):
    try:
        df = pd.read_csv("top_losers.csv")
        symbols = df['symbol'].dropna().head(top_n).tolist()
        print(f"✅ Loaded Top Losers from CSV: {len(symbols)} symbols")
        return symbols
    except Exception as e:
        print(f"❌ Failed to read top_losers.csv: {e}")
        return []

def evaluate_bullish_candidate(df):
    macd = df['MACD'].iloc[-1]
    signal = df['MACD_signal'].iloc[-1]
    rsi = df['RSI_14'].iloc[-1]
    price = df['close'].iloc[-1]
    ema200 = df['EMA_200'].iloc[-1]

    macd_diff = macd - signal
    closeness_score = int(max(min(macd_diff / 0.03, 10), -10))
    actual_diff = round(macd_diff, 3)

    volume = df['volume'].iloc[-1]
    vol_avg = df['volume'].rolling(20).mean().iloc[-1]
    volume_surge = volume >= 1.5 * vol_avg

    engulf = "Bullish Engulfing" in get_engulfing_alerts(df)

    early_volume = df['volume'].iloc[0] if not df.empty else 0
    high_early_volume = early_volume >= 900000

    green_candles = sum(df['close'].iloc[-i] > df['open'].iloc[-i] for i in range(1, 4))
    strong_momentum = green_candles >= 2

    confluence = 0
    if macd_diff < 0 and abs(macd_diff) <= 0.3:
        confluence += 1
    if rsi > 40:
        confluence += 1
    if volume_surge:
        confluence += 1
    if price > ema200:
        confluence += 1
    if engulf:
        confluence += 1

    return {
        "closeness_score": closeness_score,
        "actual_diff": actual_diff,
        "engulfing": engulf,
        "volume_surge": volume_surge,
        "rsi_ok": rsi > 40,
        "above_ema200": price > ema200,
        "rsi": round(rsi, 1),
        "volume": int(volume),
        "volume_avg": int(vol_avg),
        "confluence": confluence,
        "early_volume": early_volume,
        "high_early_volume": high_early_volume,
        "momentum": strong_momentum
    }

def run_batch(symbols_to_scan, client):
    strong, moderate, watchlist = [], [], []
    skipped = []

    for i, symbol in enumerate(symbols_to_scan):
        print(f"🔄 Scanning {symbol} ({i+1}/{len(symbols_to_scan)})...")
        df = get_stock_data(symbol, interval="15min", days=7, smart_api=client)

        if df.empty or len(df) < 35:
            print(f"⚠️ Skipped {symbol}: insufficient data")
            skipped.append(symbol)
            continue

        df = add_technical_indicators(df)
        result = evaluate_bullish_candidate(df)

        data = {
            "symbol": symbol,
            "confluence": result['confluence'],
            "closeness_score": result['closeness_score'],
            "actual_diff": result['actual_diff'],
            "rsi": result['rsi'],
            "volume": result['volume'],
            "volume_avg": result['volume_avg'],
            "volume_surge": result['volume_surge'],
            "engulfing": result['engulfing'],
            "above_ema200": result['above_ema200'],
            "early_volume": result['early_volume'],
            "high_early_volume": result['high_early_volume'],
            "momentum": result['momentum']
        }

        if result['confluence'] == 5:
            strong.append(data)
        elif result['confluence'] == 4:
            moderate.append(data)
        elif result['confluence'] == 3:
            watchlist.append(data)

        time.sleep(0.3)  # rate limit buffer

    return strong, moderate, watchlist, skipped

def report_remarks(p):
    remarks = []
    if p['high_early_volume']:
        remarks.append("High volume from open (9L+ at 9:15 AM)")
    if p['momentum']:
        remarks.append("Sustained buying momentum")
    if p['confluence'] >= 4 and p['volume_surge']:
        remarks.append("MACD gap closing with strong volume")
    return "\n" + "\n".join("• " + line for line in remarks) if remarks else ""

def main():
    print("🚀 Starting Top Losers MACD Bot (Batched)")
    client = get_smartapi_client()
    if not client:
        print("❌ SmartAPI login failed")
        return

    all_symbols = get_top_losers(top_n=9999)
    df_master = pd.read_csv("MACD_EQ_Segment_ScripMaster.csv")
    symbols_to_scan = [s for s in all_symbols if s in df_master['symbol'].values]

    total_batches = (len(symbols_to_scan) // 300) + 1
    all_strong, all_moderate, all_watchlist, all_skipped = [], [], [], []

    for b in range(total_batches):
        batch = symbols_to_scan[b * 300 : (b + 1) * 300]
        print(f"📦 Processing batch {b+1}/{total_batches} ({len(batch)} stocks)")
        strong, moderate, watchlist, skipped = run_batch(batch, client)
        all_strong += strong
        all_moderate += moderate
        all_watchlist += watchlist
        all_skipped += skipped

    if all_strong or all_moderate or all_watchlist:
        msg = "📈 <b>Bullish Candidates (Graded by Confluence)</b>\n"

        for label, items, icon, action in [
            ("Strong (5/5)", all_strong, "🟢", "✅ High Confidence"),
            ("Moderate (4/5)", all_moderate, "🟡", "⚠️ Partial Watchlist"),
            ("Watchlist (3/5)", all_watchlist, "🟠", "🔎 Observe Only")
        ]:
            if items:
                msg += f"\n{icon} <b>{label}</b>\n"
                for p in items:
                    msg += (
                        f"\n<b>{p['symbol']}</b>\n"
                        f"• MACD Closeness: {p['closeness_score']} 🔄 (actual diff: {p['actual_diff']})\n"
                        f"• RSI: {p['rsi']}\n"
                        f"• Action: {action}\n"
                        f"{report_remarks(p)}\n"
                    )

        send_telegram_message(msg)
        pd.DataFrame(all_strong + all_moderate + all_watchlist).to_csv("potential_bullish_crossover.csv", index=False)
        print("💾 Saved potential_bullish_crossover.csv")
    else:
        print("😐 No bullish setups found.")
        send_telegram_message("😐 No bullish setups found from Top Losers.")

    if all_skipped:
        pd.DataFrame(all_skipped, columns=["symbol"]).to_csv("skipped_stocks.csv", index=False)
        print(f"⚠️ Skipped {len(all_skipped)} symbols. Saved to skipped_stocks.csv")

if __name__ == "__main__":
    main()