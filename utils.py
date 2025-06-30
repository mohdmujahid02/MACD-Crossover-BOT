
import os
from dotenv import load_dotenv
load_dotenv()

import time
import pandas as pd
from datetime import datetime, timedelta
import logging
from difflib import get_close_matches
import re

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Load NSE Instruments CSV ---
instrument_df = pd.read_csv("MACD_EQ_Segment_ScripMaster.csv")

# --- Send Telegram Message (with HTML escape) ---
def send_telegram_message(message, bot_token=None, chat_id=None):
    import requests
    message = message.replace("<", "&lt;").replace(">", "&gt;")
    if bot_token is None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if chat_id is None:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        print("Telegram response:", response.status_code, "-", response.text)
    except Exception as e:
        print("❌ Failed to send Telegram message:", str(e))

# --- Get Token from CSV with fallback logic ---
def get_token_from_csv(symbol):
    try:
        instrument_df['symbol'] = instrument_df['symbol'].astype(str)
        instrument_df['instrumenttype'] = instrument_df['instrumenttype'].astype(str).fillna("EQ")
        instrument_df['exchange'] = instrument_df['exchange'].astype(str)

        # Normalize symbols
        instrument_df['normalized_symbol'] = (
            instrument_df['symbol']
            .str.replace(r'[-.].*$', '', regex=True)
            .str.replace(r'[^A-Z0-9]', '', regex=True)
            .str.upper()
        )
        symbol_upper = re.sub(r'[^A-Z0-9]', '', symbol.upper())

        # Direct match
        row = instrument_df[
            (instrument_df['normalized_symbol'] == symbol_upper) &
            (instrument_df['instrumenttype'].str.upper() == "EQ") &
            (instrument_df['exchange'].str.upper() == "NSE")
        ]
        if not row.empty:
            return str(row.iloc[0]['token'])

        # Fuzzy fallback
        matches = get_close_matches(symbol_upper, instrument_df['normalized_symbol'].unique(), n=1, cutoff=0.75)
        if matches:
            fuzzy_match = matches[0]
            print(f"ℹ️ Fuzzy matched '{symbol}' → '{fuzzy_match}'")
            row = instrument_df[instrument_df['normalized_symbol'] == fuzzy_match]
            if not row.empty:
                print(f"✅ Using token for {symbol} → {row.iloc[0]['symbol']}")
                return str(row.iloc[0]['token'])

        logger.warning(f"⚠️ Token not found for {symbol}")
        return None

    except Exception as e:
        logger.error(f"Error finding token for {symbol}: {str(e)}")
        return None

# --- Get Historical OHLC Data ---
def get_stock_data(symbol, interval="15min", days=30, smart_api=None):
    token = get_token_from_csv(symbol)
    if not token:
        return pd.DataFrame()

    time.sleep(10)

    interval_map = {
        "1min": "ONE_MINUTE", "5min": "FIVE_MINUTE",
        "15min": "FIFTEEN_MINUTE", "30min": "THIRTY_MINUTE",
        "60min": "ONE_HOUR", "1day": "ONE_DAY"
    }

    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    params = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": interval_map[interval],
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M")
    }

    try:
        response = smart_api.getCandleData(params)
        if response['status']:
            df = pd.DataFrame(response['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
            return df
        else:
            logger.error(f"SmartAPI error: {response.get('message', 'No message')}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Data fetch failed for {symbol}: {str(e)}")
        return pd.DataFrame()

# --- CSV Logger for Alerts ---
def log_alert(symbol, alert_type):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = pd.DataFrame([[now, symbol, alert_type]], columns=["timestamp", "symbol", "alert"])
    try:
        log_entry.to_csv("alerts_log.csv", mode="a", header=not os.path.exists("alerts_log.csv"), index=False)
    except Exception as e:
        logger.error(f"Error writing to alerts_log.csv: {str(e)}")
