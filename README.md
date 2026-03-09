# ⛩️ Stock Sensei

AI-powered stock intelligence dashboard built with Streamlit.

## Features
- 📊 **AI Scoring** — Each stock scored 0–100 using RSI, MACD, MA50, MA200
- 🔔 **Alert System** — Triggers on price moves or score changes
- 📈 **Technical Charts** — Candlestick + MACD + RSI in one view
- 🎯 **Signal Engine** — BUY / SELL / HOLD / WATCH signals with reasoning
- 🕵️ **Radar Breakdown** — Visual indicator score breakdown per stock

## Setup (5 minutes)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your FREE Finnhub API key
- Go to https://finnhub.io/register
- Sign up for free (takes 30 seconds)
- Copy your API key

### 3. Add your API key
Edit `.streamlit/secrets.toml`:
```toml
FINNHUB_API_KEY = "your_key_here"
```

### 4. Run the app
```bash
streamlit run app.py
```

## How the AI Score Works

| Indicator | Weight | Bullish Condition |
|-----------|--------|-------------------|
| RSI (14)  | 30 pts | RSI < 30 (oversold) |
| MACD      | 30 pts | MACD above signal line |
| MA50      | 20 pts | Price above MA50 |
| MA200     | 20 pts | Price above MA200 |

**Score → Signal:**
- 70–100 → 🟢 BUY
- 55–69  → 🔵 WATCH  
- 35–54  → 🟡 HOLD
- 0–34   → 🔴 SELL

## Alert Triggers
- Price moves ± your set threshold (default 2%)
- AI Score changes by 10+ points
- New BUY or SELL signal generated

## ⚠️ Disclaimer
Not financial advice. For educational purposes only.
