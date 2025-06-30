# position_guard_bot.py
# 🛡️ Monitors held positions for early MACD weakening signs (exit signal)

import pandas as pd
from smart_login import get_smartapi_client
from utils import get_stock_data, send_telegram_message
from indicators_correct import add_technical_indicators

def check_macd_weakness(df):
    macd_now = df['MACD'].iloc[-1]
    signal_now = df['MACD_signal'].iloc[-1]
    macd_prev = df['MACD'].iloc[-2]
    signal_prev = df['MACD_signal'].iloc[-2]

    # Early weakness: MACD is above signal but difference is shrinking
    gap_now = macd_now - signal_now
    gap_prev = macd_prev - signal_prev

    if gap_now > 0 and gap_now < gap_prev and gap_now < 0.1:
        return True, round(gap_now, 3)
    return False, round(gap_now, 3)

def main():
    print("🛡️ Position Guard Bot - Checking for MACD Weakness")
    client = get_smartapi_client()
    if not client:
        print("❌ Login failed")
        return

    try:
        df_pos = pd.read_csv("my_positions.csv")
        held_symbols = df_pos['symbol'].dropna().tolist()
        print(f"📦 Watching positions: {held_symbols}")
    except Exception as e:
        print(f"❌ Failed to read my_positions.csv: {e}")
        return

    for symbol in held_symbols:
        df = get_stock_data(symbol, interval="15min", days=5, smart_api=client)
        if df.empty or len(df) < 35:
            continue

        df = add_technical_indicators(df)
        flag, gap = check_macd_weakness(df)

        if flag:
            msg = (
                f"⚠️ <b>MACD Weakening Alert</b>\n"
                f"Symbol: <b>{symbol}</b>\n"
                f"Gap: {gap} (shrinking)\n"
                f"🔍 MACD bullish trend weakening. Monitor position closely."
            )
            send_telegram_message(msg)
            print(f"⚠️ Exit warning sent for {symbol}")

    print("✅ Position check complete.")

if __name__ == "__main__":
    main()
