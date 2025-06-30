# 📈 MACD Swing Trade BOT

A complete semi-automated swing trading pipeline for NSE stocks — powered by technical and fundamental filters.  
It scans oversold stocks for potential bullish reversals, scores them, and delivers signals via Telegram.

---

## 🚀 Features

✅ Pulls Top Losers from NSE manually or TradingView  
✅ Calculates MACD crossovers, RSI, EMA, Volume Surges, Engulfing patterns  
✅ Adds Fundamentals: Promoter Holding, Debt/Equity, P/E, ROE  
✅ Generates Confluence Score (up to 5) for easy grading  
✅ Sends clear daily reports to Telegram  
✅ Includes Position Guard BOT to monitor held stocks for early bearish signs

---

## 📂 Files Included

- `top_losers_macd_bot.py` — main entry BOT to scan oversold stocks
- `fundamentals_scraper.py` — enriches signals with Screener.in data
- `final_report_sender.py` — formats and sends final daily summary to Telegram
- `position_guard_bot.py` — watches your held trades for exit triggers
- `utils.py` — helper functions for SmartAPI, Telegram, etc.
- `indicators_correct.py` — technical indicator logic
- `smart_login.py` — handles SmartAPI login
- `MACD_EQ_Segment_ScripMaster.csv` — NSE segment master file
- `top_losers.csv` — your daily input file (sample)
- `my_positions.csv` — positions tracker (sample)

---

## ⚙️ Setup

1️⃣ Clone this repo  
2️⃣ Install dependencies  
```bash
pip install -r requirements.txt

