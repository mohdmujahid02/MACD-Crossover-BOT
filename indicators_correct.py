import pandas as pd
import numpy as np
import pandas_ta as ta

def add_technical_indicators(df):
    df['EMA_5'] = ta.ema(df['close'], length=5)
    df['EMA_13'] = ta.ema(df['close'], length=13)
    df['EMA_21'] = ta.ema(df['close'], length=21)
    df['RSI_14'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_signal'] = macd['MACDs_12_26_9']
    df['MACD_hist'] = macd['MACDh_12_26_9']
    return df

def get_engulfing_alerts(df):
    if len(df) < 2:
        return []
    last = df.iloc[-1]
    prev = df.iloc[-2]
    alerts = []

    if last['close'] > last['open'] and prev['close'] < prev['open']:
        if last['open'] < prev['close'] and last['close'] > prev['open']:
            alerts.append("Bullish Engulfing")

    elif last['close'] < last['open'] and prev['close'] > prev['open']:
        if last['open'] > prev['close'] and last['close'] < prev['open']:
            alerts.append("Bearish Engulfing")

    return alerts

def macd_crossover(df):
    if 'MACD' not in df.columns or 'MACD_signal' not in df.columns:
        return None

    recent = df.iloc[-2:]
    prev_macd = recent.iloc[0]['MACD']
    prev_signal = recent.iloc[0]['MACD_signal']
    curr_macd = recent.iloc[1]['MACD']
    curr_signal = recent.iloc[1]['MACD_signal']

    if prev_macd < prev_signal and curr_macd > curr_signal:
        return True  # Bullish crossover
    elif prev_macd > prev_signal and curr_macd < curr_signal:
        return False  # Bearish crossover
    else:
        return None  # No signal

def calculate_trend_strength(df):
    if df.empty or len(df) < 5:
        return False, 0
    latest = df.iloc[-1]
    emas = [latest['EMA_5'], latest['EMA_13'], latest['EMA_21']]
    price = latest['close']
    count = sum(price > ema for ema in emas)
    strength = count / len(emas)
    return (strength >= 0.66), round(strength, 2)

def analyze_candle_strength(df):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    range_ = last['high'] - last['low']
    body_ratio = body / range_ if range_ > 0 else 0
    close_position = (last['high'] - last['close']) / range_ if range_ > 0 else 1
    volume_ratio = last['volume'] / df['volume'].rolling(10).mean().iloc[-1] if 'volume' in df.columns else 1

    return {
        'body_ratio': round(body_ratio, 2),
        'close_position': round(close_position, 2),
        'volume_ratio': round(volume_ratio, 2)
    }
