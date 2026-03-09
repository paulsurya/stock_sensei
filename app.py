import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import finnhub
import json
import time
from datetime import datetime, timedelta
import os

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Sensei",
    page_icon="⛩️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global */
html, body, [class*="css"] { font-family: 'Syne', sans-serif !important; }
.stApp { background: #04080f; color: #e2e8f0; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #080d18 !important;
    border-right: 1px solid #1a2540 !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Main background */
.main .block-container { padding-top: 1.5rem; max-width: 1400px; }

/* Metric cards */
.metric-card {
    background: #080d18;
    border: 1px solid #1a2540;
    border-radius: 12px;
    padding: 18px 20px;
    transition: border-color 0.2s, transform 0.2s;
}
.metric-card:hover { border-color: #f0b429; transform: translateY(-2px); }
.metric-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 3px; color: #475569; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-size: 26px; font-weight: 800; }
.metric-sub { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b; margin-top: 4px; }
.green { color: #10d991; }
.red { color: #f43f5e; }
.gold { color: #f0b429; }
.blue { color: #3b82f6; }

/* Score badge */
.score-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 52px; height: 52px; border-radius: 50%;
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px; font-weight: 700;
    border: 2px solid;
}

/* Signal pill */
.signal-buy   { background: rgba(16,217,145,0.12); color: #10d991; border: 1px solid rgba(16,217,145,0.3); padding: 3px 12px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.signal-sell  { background: rgba(244,63,94,0.12);  color: #f43f5e; border: 1px solid rgba(244,63,94,0.3);  padding: 3px 12px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.signal-hold  { background: rgba(240,180,41,0.12); color: #f0b429; border: 1px solid rgba(240,180,41,0.3); padding: 3px 12px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.signal-watch { background: rgba(59,130,246,0.12); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); padding: 3px 12px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1px; }

/* Alert card */
.alert-card { background: #080d18; border-left: 3px solid; border-radius: 0 10px 10px 0; padding: 12px 16px; margin-bottom: 10px; }
.alert-up   { border-color: #10d991; }
.alert-down { border-color: #f43f5e; }
.alert-info { border-color: #3b82f6; }
.alert-title { font-weight: 700; font-size: 13px; margin-bottom: 2px; }
.alert-desc  { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b; }

/* Section header */
.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 4px; color: #f0b429;
    text-transform: uppercase; margin-bottom: 12px;
    padding-bottom: 8px; border-bottom: 1px solid #1a2540;
}

/* Indicator row */
.indicator-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.indicator-chip {
    background: #0d1420; border: 1px solid #1a2540;
    border-radius: 8px; padding: 8px 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}
.indicator-chip .i-label { color: #475569; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; }
.indicator-chip .i-value { font-weight: 700; font-size: 14px; margin-top: 2px; }

/* Logo */
.logo-text {
    font-size: 22px; font-weight: 800; letter-spacing: 3px;
    color: #f0b429; padding: 8px 0 24px;
}

/* Stmetics override */
[data-testid="metric-container"] { background: #080d18; border: 1px solid #1a2540; border-radius: 12px; padding: 16px; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; color: #e2e8f0 !important; }
[data-testid="stMetricLabel"] { color: #475569 !important; font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "last_prices" not in st.session_state:
    st.session_state.last_prices = {}
if "alert_threshold" not in st.session_state:
    st.session_state.alert_threshold = 2.0

# ── FINNHUB CLIENT ────────────────────────────────────────────────────────────
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "YOUR_FINNHUB_API_KEY_HERE")

@st.cache_resource
def get_finnhub_client():
    return finnhub.Client(api_key=FINNHUB_API_KEY)

def get_quote_finnhub(ticker: str) -> dict:
    """Get real-time quote from Finnhub."""
    try:
        fc = get_finnhub_client()
        q = fc.quote(ticker)
        return q
    except Exception:
        return {}

def get_company_profile(ticker: str) -> dict:
    """Get company profile from Finnhub."""
    try:
        fc = get_finnhub_client()
        return fc.company_profile2(symbol=ticker)
    except Exception:
        return {}

# ── YFINANCE DATA ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch OHLCV history from yfinance."""
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

# ── TECHNICAL INDICATORS ──────────────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute RSI, MACD, MA50, MA200 from OHLCV dataframe."""
    if df.empty or len(df) < 30:
        return {}
    close = df["Close"].squeeze()
    indicators = {}
    # RSI
    rsi_series = compute_rsi(close)
    indicators["rsi"] = round(float(rsi_series.iloc[-1]), 2)
    indicators["rsi_series"] = rsi_series
    # MACD
    macd, signal, hist = compute_macd(close)
    indicators["macd"] = round(float(macd.iloc[-1]), 4)
    indicators["macd_signal"] = round(float(signal.iloc[-1]), 4)
    indicators["macd_hist"] = round(float(hist.iloc[-1]), 4)
    indicators["macd_series"] = macd
    indicators["macd_signal_series"] = signal
    indicators["macd_hist_series"] = hist
    # MA50
    if len(close) >= 50:
        ma50 = close.rolling(50).mean()
        indicators["ma50"] = round(float(ma50.iloc[-1]), 2)
        indicators["ma50_series"] = ma50
    # MA200
    if len(close) >= 200:
        ma200 = close.rolling(200).mean()
        indicators["ma200"] = round(float(ma200.iloc[-1]), 2)
        indicators["ma200_series"] = ma200
    indicators["close"] = float(close.iloc[-1])
    indicators["close_series"] = close
    indicators["df"] = df
    return indicators

# ── AI SCORING ENGINE ─────────────────────────────────────────────────────────
def compute_score(indicators: dict) -> dict:
    """
    Score a stock 0-100 using RSI, MACD, MA50, MA200.
    Returns score, breakdown, signal, and reasoning.
    """
    if not indicators:
        return {"score": 50, "signal": "hold", "breakdown": {}, "reasoning": []}

    score = 0
    breakdown = {}
    reasoning = []

    # ── RSI (30 pts) ──────────────────────────────────────────────────────────
    rsi = indicators.get("rsi", 50)
    if rsi < 30:
        rsi_score = 28
        reasoning.append(f"RSI {rsi:.1f} — Oversold territory, strong bounce potential 🟢")
    elif rsi < 40:
        rsi_score = 22
        reasoning.append(f"RSI {rsi:.1f} — Approaching oversold, accumulation zone 🟡")
    elif rsi < 55:
        rsi_score = 17
        reasoning.append(f"RSI {rsi:.1f} — Neutral zone, no strong signal ⚪")
    elif rsi < 70:
        rsi_score = 12
        reasoning.append(f"RSI {rsi:.1f} — Overbought approaching, caution ⚠️")
    else:
        rsi_score = 5
        reasoning.append(f"RSI {rsi:.1f} — Severely overbought, high reversal risk 🔴")
    breakdown["RSI"] = {"score": rsi_score, "max": 30, "value": rsi}
    score += rsi_score

    # ── MACD (30 pts) ─────────────────────────────────────────────────────────
    macd = indicators.get("macd", 0)
    macd_signal = indicators.get("macd_signal", 0)
    macd_hist = indicators.get("macd_hist", 0)
    if macd > macd_signal and macd_hist > 0:
        macd_score = 28
        reasoning.append(f"MACD bullish crossover — momentum accelerating upward 🟢")
    elif macd > macd_signal:
        macd_score = 20
        reasoning.append(f"MACD above signal — positive trend building 🟡")
    elif macd < macd_signal and macd_hist < 0:
        macd_score = 6
        reasoning.append(f"MACD bearish crossover — downward momentum confirmed 🔴")
    else:
        macd_score = 13
        reasoning.append(f"MACD mixed signals — trend not clearly defined ⚪")
    breakdown["MACD"] = {"score": macd_score, "max": 30, "value": round(macd, 4)}
    score += macd_score

    # ── MA50 (20 pts) ─────────────────────────────────────────────────────────
    close = indicators.get("close", 0)
    ma50 = indicators.get("ma50")
    if ma50:
        if close > ma50 * 1.03:
            ma50_score = 18
            reasoning.append(f"Price ${close:.2f} well above MA50 ${ma50:.2f} — bullish trend 🟢")
        elif close > ma50:
            ma50_score = 13
            reasoning.append(f"Price above MA50 — short-term uptrend intact 🟡")
        elif close > ma50 * 0.97:
            ma50_score = 8
            reasoning.append(f"Price near MA50 — potential support test ⚪")
        else:
            ma50_score = 3
            reasoning.append(f"Price below MA50 — short-term downtrend 🔴")
        breakdown["MA50"] = {"score": ma50_score, "max": 20, "value": ma50}
        score += ma50_score
    else:
        breakdown["MA50"] = {"score": 10, "max": 20, "value": None}
        score += 10

    # ── MA200 (20 pts) ────────────────────────────────────────────────────────
    ma200 = indicators.get("ma200")
    if ma200:
        if close > ma200 * 1.05:
            ma200_score = 18
            reasoning.append(f"Price well above MA200 — strong long-term bullish 🟢")
        elif close > ma200:
            ma200_score = 13
            reasoning.append(f"Price above MA200 — long-term uptrend confirmed 🟡")
        elif close > ma200 * 0.95:
            ma200_score = 7
            reasoning.append(f"Price slightly below MA200 — long-term trend weakening ⚪")
        else:
            ma200_score = 2
            reasoning.append(f"Price far below MA200 — bearish long-term outlook 🔴")
        breakdown["MA200"] = {"score": ma200_score, "max": 20, "value": ma200}
        score += ma200_score
    else:
        breakdown["MA200"] = {"score": 10, "max": 20, "value": None}
        score += 10

    score = max(0, min(100, score))

    # ── Signal ────────────────────────────────────────────────────────────────
    if score >= 70:
        signal = "buy"
    elif score >= 55:
        signal = "watch"
    elif score >= 35:
        signal = "hold"
    else:
        signal = "sell"

    return {"score": score, "signal": signal, "breakdown": breakdown, "reasoning": reasoning}

def score_color(score: int) -> str:
    if score >= 70: return "#10d991"
    if score >= 45: return "#f0b429"
    return "#f43f5e"

def signal_html(signal: str) -> str:
    labels = {"buy": "BUY", "sell": "SELL", "hold": "HOLD", "watch": "WATCH"}
    return f'<span class="signal-{signal}">{labels.get(signal, signal.upper())}</span>'

# ── ALERT ENGINE ──────────────────────────────────────────────────────────────
def check_alerts(ticker: str, current_price: float, pct_change: float, score: int, signal: str):
    threshold = st.session_state.alert_threshold
    alerts = []
    last = st.session_state.last_prices.get(ticker)
    
    # Store alert types for this ticker to prevent duplicates
    if "alert_history" not in st.session_state:
        st.session_state.alert_history = {}
    if ticker not in st.session_state.alert_history:
        st.session_state.alert_history[ticker] = set()

    # 1. Price Move Alert
    if abs(pct_change) >= threshold:
        direction = "up" if pct_change > 0 else "down"
        alert_id = f"move_{direction}_{int(pct_change*10)}" # Granular alert ID
        if alert_id not in st.session_state.alert_history[ticker]:
            alerts.append({
                "ticker": ticker,
                "type": direction,
                "title": f"{ticker} moved {pct_change:+.2f}%",
                "desc": f"Price: ${current_price:.2f} | Threshold: ±{threshold}%",
                "time": datetime.now().strftime("%H:%M:%S"),
                "score": score,
                "signal": signal,
            })
            st.session_state.alert_history[ticker].add(alert_id)

    # 2. AI Score Change Alert
    if last:
        prev_score = last.get("score", 50)
        if abs(score - prev_score) >= 10:
            direction = "up" if score > prev_score else "down"
            alert_id = f"score_{direction}_{score}"
            if alert_id not in st.session_state.alert_history[ticker]:
                alerts.append({
                    "ticker": ticker,
                    "type": direction,
                    "title": f"{ticker} AI Score changed: {prev_score} → {score}",
                    "desc": f"New signal: {signal.upper()} | Price: ${current_price:.2f}",
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "score": score,
                    "signal": signal,
                })
                st.session_state.alert_history[ticker].add(alert_id)

    # 3. Signal Trigger Alert
    if signal in ("buy", "sell") and last and last.get("signal") not in ("buy", "sell"):
        alert_id = f"signal_{signal}"
        if alert_id not in st.session_state.alert_history[ticker]:
            alerts.append({
                "ticker": ticker,
                "type": "up" if signal == "buy" else "down",
                "title": f"🚨 {ticker} triggered {signal.upper()} signal!",
                "desc": f"Score: {score}/100 | Price: ${current_price:.2f}",
                "time": datetime.now().strftime("%H:%M:%S"),
                "score": score,
                "signal": signal,
            })
            st.session_state.alert_history[ticker].add(alert_id)

    st.session_state.last_prices[ticker] = {"price": current_price, "score": score, "signal": signal}
    return alerts

# ── CHART BUILDERS ────────────────────────────────────────────────────────────
def build_price_chart(df: pd.DataFrame, ticker: str, indicators: dict) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.03,
        subplot_titles=["", "MACD", "RSI"]
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"].squeeze(), high=df["High"].squeeze(),
        low=df["Low"].squeeze(), close=df["Close"].squeeze(),
        name=ticker,
        increasing_line_color="#10d991", decreasing_line_color="#f43f5e",
        increasing_fillcolor="rgba(16, 217, 145, 0.2)", decreasing_fillcolor="rgba(244, 63, 94, 0.2)",
    ), row=1, col=1)

    # MA50
    if "ma50_series" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["ma50_series"],
            name="MA50", line=dict(color="#f0b429", width=1.5, dash="dot"),
            opacity=0.9,
        ), row=1, col=1)

    # MA200
    if "ma200_series" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["ma200_series"],
            name="MA200", line=dict(color="#3b82f6", width=1.5, dash="dash"),
            opacity=0.9,
        ), row=1, col=1)

    # MACD
    if "macd_series" in indicators:
        hist = indicators["macd_hist_series"]
        colors = ["#10d991" if v >= 0 else "#f43f5e" for v in hist]
        fig.add_trace(go.Bar(
            x=df.index, y=hist, name="MACD Hist",
            marker_color=colors, opacity=0.7,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["macd_series"],
            name="MACD", line=dict(color="#f0b429", width=1.5),
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["macd_signal_series"],
            name="Signal", line=dict(color="#3b82f6", width=1.5),
        ), row=2, col=1)

    # RSI
    if "rsi_series" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["rsi_series"],
            name="RSI", line=dict(color="#a78bfa", width=2),
            fill="tozeroy", fillcolor="rgba(167,139,250,0.08)",
        ), row=3, col=1)
        fig.add_hline(y=70, line_color="#f43f5e", line_dash="dot", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_color="#10d991", line_dash="dot", line_width=1, row=3, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#04080f", plot_bgcolor="#04080f",
        font=dict(family="JetBrains Mono, monospace", color="#64748b", size=11),
        height=540,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            bgcolor="#080d18", bordercolor="#1a2540", borderwidth=1,
            font=dict(size=10), orientation="h", y=1.02,
        ),
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#1a2540", row=i, col=1, showline=False)
        fig.update_yaxes(gridcolor="#1a2540", row=i, col=1, showline=False)

    return fig

def build_score_gauge(score: int, ticker: str) -> go.Figure:
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"{ticker} AI Score", "font": {"color": "#64748b", "size": 13, "family": "JetBrains Mono"}},
        number={"font": {"color": color, "size": 48, "family": "JetBrains Mono"}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#1a2540", "tickfont": {"color": "#475569", "size": 10}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#080d18",
            "bordercolor": "#1a2540",
            "steps": [
                {"range": [0, 35],  "color": "rgba(244,63,94,0.15)"},
                {"range": [35, 55], "color": "rgba(240,180,41,0.10)"},
                {"range": [55, 70], "color": "rgba(240,180,41,0.15)"},
                {"range": [70, 100], "color": "rgba(16,217,145,0.15)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score},
        },
    ))
    fig.update_layout(
        paper_bgcolor="#04080f", font=dict(color="#e2e8f0"),
        height=220, margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig

def build_radar_chart(breakdown: dict) -> go.Figure:
    if not breakdown:
        return go.Figure()
    categories = list(breakdown.keys())
    scores = [v["score"] / v["max"] * 100 for v in breakdown.values()]
    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]
    fig = go.Figure(go.Scatterpolar(
        r=scores_closed, theta=categories_closed,
        fill="toself", fillcolor="rgba(240,180,41,0.1)",
        line=dict(color="#f0b429", width=2),
        marker=dict(size=6, color="#f0b429"),
        name="Score Breakdown",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#04080f",
            radialaxis=dict(visible=True, range=[0, 100], color="#1a2540", gridcolor="#1a2540", tickfont=dict(size=9, color="#475569")),
            angularaxis=dict(color="#475569", gridcolor="#1a2540"),
        ),
        paper_bgcolor="#04080f",
        font=dict(color="#e2e8f0", family="JetBrains Mono"),
        height=220, margin=dict(l=30, r=30, t=30, b=10),
        showlegend=False,
    )
    return fig

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-text">⛩️ STOCK SENSEI</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">// WATCHLIST</div>', unsafe_allow_html=True)
    new_ticker = st.text_input("Add ticker", placeholder="e.g. GOOGL", key="add_ticker").upper().strip()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("＋ Add", use_container_width=True):
            if new_ticker and new_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker)
                st.rerun()
    with col2:
        if st.button("✕ Remove", use_container_width=True):
            if new_ticker in st.session_state.watchlist:
                st.session_state.watchlist.remove(new_ticker)
                st.rerun()

    st.markdown("**Current watchlist:**")
    for t in st.session_state.watchlist:
        st.markdown(f"&nbsp;&nbsp;`{t}`")

    st.divider()
    st.markdown('<div class="section-header">// ALERT SETTINGS</div>', unsafe_allow_html=True)
    st.session_state.alert_threshold = st.slider(
        "Price change threshold (%)", 0.5, 10.0,
        st.session_state.alert_threshold, 0.5,
        help="Trigger alert when price moves more than this %"
    )
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)

    st.divider()
    st.markdown('<div class="section-header">// CHART PERIOD</div>', unsafe_allow_html=True)
    chart_period = st.selectbox("History period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
  <div>
    <div style="font-size:28px;font-weight:800;color:#f0b429;letter-spacing:3px;">STOCK SENSEI</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#475569;letter-spacing:3px;margin-top:4px;">// AI-POWERED STOCK INTELLIGENCE</div>
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#1a2540;padding:8px 16px;border:1px solid #1a2540;border-radius:8px;">
    LIVE DASHBOARD
  </div>
</div>
""", unsafe_allow_html=True)

# ── LOAD ALL STOCK DATA ───────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_stock_data(ticker: str, period: str):
    df = get_history(ticker, period)
    indicators = compute_indicators(df)
    score_data = compute_score(indicators)
    quote = get_quote_finnhub(ticker)
    return df, indicators, score_data, quote

all_data = {}
progress = st.progress(0, text="Loading market data...")
for i, ticker in enumerate(st.session_state.watchlist):
    df, indicators, score_data, quote = load_stock_data(ticker, chart_period)
    all_data[ticker] = {"df": df, "indicators": indicators, "score_data": score_data, "quote": quote}
    progress.progress((i + 1) / len(st.session_state.watchlist), text=f"Loaded {ticker}...")
progress.empty()

# ── ALERT CHECKING ────────────────────────────────────────────────────────────
new_alerts = []
for ticker, data in all_data.items():
    q = data["quote"]
    sd = data["score_data"]
    if q and q.get("c"):
        current_price = q["c"]
        pct_change = q.get("dp", 0) or 0
        alerts = check_alerts(ticker, current_price, pct_change, sd["score"], sd["signal"])
        new_alerts.extend(alerts)

if new_alerts:
    st.session_state.alerts = (new_alerts + st.session_state.alerts)[:20]

# ── TOP STATS ROW ─────────────────────────────────────────────────────────────
scores_all = [d["score_data"]["score"] for d in all_data.values()]
buy_count  = sum(1 for d in all_data.values() if d["score_data"]["signal"] == "buy")
sell_count = sum(1 for d in all_data.values() if d["score_data"]["signal"] == "sell")
avg_score  = int(np.mean(scores_all)) if scores_all else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Stocks Tracked</div>
      <div class="metric-value gold">{len(st.session_state.watchlist)}</div>
      <div class="metric-sub">in watchlist</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Avg AI Score</div>
      <div class="metric-value" style="color:{score_color(avg_score)}">{avg_score}</div>
      <div class="metric-sub">out of 100</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Buy Signals</div>
      <div class="metric-value green">{buy_count}</div>
      <div class="metric-sub">active today</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Sell Signals</div>
      <div class="metric-value red">{sell_count}</div>
      <div class="metric-sub">active today</div>
    </div>""", unsafe_allow_html=True)
with c5:
    alert_count = len(st.session_state.alerts)
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Active Alerts</div>
      <div class="metric-value {'red' if alert_count > 0 else 'gold'}">{alert_count}</div>
      <div class="metric-sub">since last check</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── MAIN TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Watchlist & Scores", "📈  Chart Analysis", "🔔  Alerts"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — WATCHLIST & SCORES
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">// AI STOCK SCORES</div>', unsafe_allow_html=True)

    for ticker, data in all_data.items():
        q    = data["quote"]
        sd   = data["score_data"]
        ind  = data["indicators"]
        score = sd["score"]
        signal = sd["signal"]
        color = score_color(score)

        # Pull price info
        price     = q.get("c", 0) if q else ind.get("close", 0)
        pct_chg   = q.get("dp", 0) if q else 0
        day_high  = q.get("h", 0) if q else 0
        day_low   = q.get("l", 0) if q else 0
        prev_close = q.get("pc", 0) if q else 0

        with st.expander(f"**{ticker}**  —  ${price:.2f}  {'▲' if pct_chg >= 0 else '▼'} {abs(pct_chg):.2f}%  |  Score: {score}/100", expanded=True):
            row1, row2, row3 = st.columns([1, 2, 2])

            with row1:
                st.plotly_chart(build_score_gauge(score, ticker), use_container_width=True, config={"displayModeBar": False}, key=f"gauge_{ticker}")
                st.markdown(f"<div style='text-align:center;margin-top:-10px'>{signal_html(signal)}</div>", unsafe_allow_html=True)

            with row2:
                st.markdown('<div class="section-header">// INDICATOR BREAKDOWN</div>', unsafe_allow_html=True)
                for ind_name, val in sd["breakdown"].items():
                    bar_pct = val["score"] / val["max"] * 100
                    bar_color = score_color(int(bar_pct))
                    v = val["value"]
                    v_str = f"{v:.2f}" if v is not None else "N/A"
                    st.markdown(f"""
                    <div style="margin-bottom:14px;">
                      <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#64748b;letter-spacing:2px;">{ind_name}</span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:{bar_color};font-weight:700;">{val['score']}/{val['max']} &nbsp;·&nbsp; {v_str}</span>
                      </div>
                      <div style="background:#1a2540;border-radius:4px;height:6px;overflow:hidden;">
                        <div style="width:{bar_pct}%;height:100%;background:{bar_color};border-radius:4px;transition:width 0.5s;"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                if "breakdown" in sd:
                    st.plotly_chart(build_radar_chart(sd["breakdown"]), use_container_width=True, config={"displayModeBar": False}, key=f"radar_{ticker}")

            with row3:
                st.markdown('<div class="section-header">// AI REASONING</div>', unsafe_allow_html=True)
                for reason in sd["reasoning"]:
                    st.markdown(f"""<div style="background:#080d18;border:1px solid #1a2540;border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:12px;line-height:1.6;">{reason}</div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-header" style="margin-top:16px;">// MARKET DATA</div>', unsafe_allow_html=True)
                mc1, mc2 = st.columns(2)
                with mc1:
                    st.markdown(f"""
                    <div class="indicator-chip"><div class="i-label">Day High</div><div class="i-value green">${day_high:.2f}</div></div>
                    <div class="indicator-chip" style="margin-top:8px;"><div class="i-label">Prev Close</div><div class="i-value">${prev_close:.2f}</div></div>
                    """, unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""
                    <div class="indicator-chip"><div class="i-label">Day Low</div><div class="i-value red">${day_low:.2f}</div></div>
                    <div class="indicator-chip" style="margin-top:8px;"><div class="i-label">RSI</div><div class="i-value" style="color:{'#f43f5e' if ind.get('rsi',50) > 70 else '#10d991' if ind.get('rsi',50) < 30 else '#f0b429'}">{ind.get('rsi', 'N/A')}</div></div>
                    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — CHART ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">// TECHNICAL CHART</div>', unsafe_allow_html=True)
    selected = st.selectbox("Select stock", st.session_state.watchlist, key="chart_select")
    data = all_data.get(selected, {})
    df = data.get("df", pd.DataFrame())
    indicators = data.get("indicators", {})

    if not df.empty:
        st.plotly_chart(build_price_chart(df, selected, indicators), use_container_width=True, config={"displayModeBar": False}, key=f"main_chart_{selected}")

        # Key stats below chart
        q = data["quote"]
        s = data["score_data"]
        st.markdown('<div class="section-header">// KEY STATISTICS</div>', unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        stats = [
            ("Current Price", f"${q.get('c',0):.2f}" if q else "N/A", "#e2e8f0"),
            ("RSI (14)", f"{indicators.get('rsi','N/A')}", "#a78bfa"),
            ("MACD", f"{indicators.get('macd','N/A')}", "#f0b429"),
            ("MA50",  f"${indicators.get('ma50',0):.2f}" if indicators.get('ma50') else "N/A", "#f0b429"),
            ("MA200", f"${indicators.get('ma200',0):.2f}" if indicators.get('ma200') else "N/A", "#3b82f6"),
        ]
        for col, (label, value, color) in zip([k1,k2,k3,k4,k5], stats):
            with col:
                st.markdown(f"""<div class="metric-card" style="text-align:center;">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value" style="color:{color};font-size:18px;">{value}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.warning(f"No data available for {selected}. Check the ticker symbol.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — ALERTS
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<div class="section-header">// ACTIVE ALERTS</div>', unsafe_allow_html=True)
        if not st.session_state.alerts:
            st.markdown("""<div style="background:#080d18;border:1px solid #1a2540;border-radius:12px;padding:32px;text-align:center;color:#475569;">
              <div style="font-size:32px;margin-bottom:12px;">🔕</div>
              <div style="font-family:'JetBrains Mono',monospace;letter-spacing:2px;font-size:12px;">NO ALERTS YET</div>
              <div style="font-size:12px;margin-top:8px;">Alerts trigger when price moves ±{:.1f}% or AI score changes significantly</div>
            </div>""".format(st.session_state.alert_threshold), unsafe_allow_html=True)
        else:
            if st.button("🗑️ Clear all alerts"):
                st.session_state.alerts = []
                st.rerun()
            for alert in st.session_state.alerts:
                icon = "▲" if alert["type"] == "up" else "▼"
                color = "#10d991" if alert["type"] == "up" else "#f43f5e"
                st.markdown(f"""
                <div class="alert-card alert-{'up' if alert['type'] == 'up' else 'down'}">
                  <div class="alert-title" style="color:{color};">{icon} {alert['title']}</div>
                  <div class="alert-desc">{alert['desc']} &nbsp;·&nbsp; {alert['time']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-header">// SIGNAL SUMMARY</div>', unsafe_allow_html=True)
        for ticker, data in all_data.items():
            sd = data["score_data"]
            q  = data["quote"]
            price = q.get("c", 0) if q else data["indicators"].get("close", 0)
            pct   = q.get("dp", 0) if q else 0
            color = score_color(sd["score"])
            st.markdown(f"""
            <div style="background:#080d18;border:1px solid #1a2540;border-radius:10px;padding:12px 16px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;">
              <div>
                <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#f0b429;">{ticker}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#475569;">${price:.2f} &nbsp; {'▲' if pct>=0 else '▼'} {abs(pct):.2f}%</div>
              </div>
              <div style="text-align:right;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:800;color:{color};">{sd['score']}</div>
                {signal_html(sd['signal'])}
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
# ── AUTO-REFRESH ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()

st.markdown("""
<div style="margin-top:48px;padding:20px 0;border-top:1px solid #1a2540;text-align:center;font-family:'JetBrains Mono',monospace;font-size:10px;color:#1a2540;letter-spacing:3px;">
  STOCK SENSEI · AI SCORING ENGINE · NOT FINANCIAL ADVICE
</div>
""", unsafe_allow_html=True)
