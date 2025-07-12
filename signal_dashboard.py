import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
#import winsound
import plotly.io as pio

from ou_stop_calc import ornstein_uhlenbeck
from discord_alert import send_discord_alert

# ========== DASHBOARD CONFIG ==========
st.set_page_config(layout="wide")
st.title("📊 BTC Scalper Signal Dashboard — Final v4.5")

# ========== LOAD SIGNAL DATA ==========
df = pd.read_csv("signal_output.csv")
last = df.iloc[-1]
last_close = last["close"]

# ========== CHART SETUP ==========
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candles"))

fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_upper'], name="Upper Band", line=dict(color="red")))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_lower'], name="Lower Band", line=dict(color="green")))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['vwap'], name="VWAP", line=dict(color="blue")))

# Calculate OU-based SL/TP
mean_price, ou_stop = ornstein_uhlenbeck(df["close"])
safe_stop = max(ou_stop, last_close * 0.005)
sl = round(last_close - safe_stop, 2)
tp = round(last_close + 1.5 * safe_stop, 2)

fig.add_trace(go.Scatter(x=df['timestamp'], y=[sl]*len(df), name="Stop Loss", line=dict(color="orange", dash='dot')))
fig.add_trace(go.Scatter(x=df['timestamp'], y=[tp]*len(df), name="Take Profit", line=dict(color="purple", dash='dot')))

st.plotly_chart(fig, use_container_width=True)

# Save chart as PNG
try:
    chart_path = "chart.png"
    pio.write_image(fig, chart_path, format="png", width=1000, height=500, scale=2)
except Exception as e:
    chart_path = None
    st.warning(f"⚠️ Chart image not saved: {e}")

# ========== SIGNAL INFO ==========
latest_signal = last["signal"]
st.subheader(f"📢 Signal: {latest_signal}")

# ========== OFI DATA LOADER ==========
ofi = 0
try:
    ofi_df = pd.read_csv("ofi_output.csv")
    ofi = round(ofi_df['ofi'].iloc[-1], 2)
    st.metric("📊 Order Flow Imbalance (OFI)", value=ofi)
except:
    st.warning("No OFI data found.")

# ========== CONFIDENCE SCORE ==========
confidence = "🟡 Neutral"
if "Long" in latest_signal and ofi > 5:
    confidence = "🟢 Strong Long"
    #winsound.Beep(880, 200)
elif "Short" in latest_signal and ofi < -5:
    confidence = "🔴 Strong Short"
    winsound.Beep(660, 200)

st.markdown(f"### ⚡ Confidence: **{confidence}**")
st.progress(min(abs(ofi)/10, 1.0))

# ========== TRADE PLAN OUTPUT ==========
st.subheader("📋 Trade Plan")
st.markdown(f"- 💹 Entry: `{last_close}`")
st.markdown(f"- 🛡️ SL: `{sl}`")
st.markdown(f"- 🎯 TP: `{tp}`")
st.markdown(f"- 📊 OFI: `{ofi}`")

# ========== POSITION SIZING ==========
st.subheader("📐 Position Sizing")

capital = st.number_input("Account Balance ($)", min_value=100.0, value=1000.0)
risk_pct = st.slider("Risk %", 0.1, 5.0, step=0.1, value=1.0)

risk_amt = (risk_pct / 100) * capital
sl_diff = abs(last_close - sl)
position_size = round(risk_amt / sl_diff, 6) if sl_diff != 0 else 0

st.markdown(f"- 💰 Risk: `{risk_amt:.2f}` USD")
st.markdown(f"- 🔢 Size: `{position_size}` Units")

# ========== DISCORD ALERT ==========
webhook_url = "https://discord.com/api/webhooks/1393523876222468166/B606YjDM7HDpVonrWiDQZGyTOmIMopcE5datFGhNAJZ-G04pNkav89fPYLwCktrAJBzl"   # Replace with your URL
dashboard_url = "http://localhost:8504/"

if ("Long" in latest_signal and ofi > 5) or ("Short" in latest_signal and ofi < -5):
    send_discord_alert(
        webhook_url=webhook_url,
        signal=latest_signal,
        entry=round(last_close, 2),
        sl=sl, tp=tp, ofi=ofi,
        confidence=confidence,
        chart_image_path=chart_path,
        dashboard_link=dashboard_url
    )

# ========== TRADE LOG BUTTON ==========
if st.button("✅ Log Trade Now (Manual Click)"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt_entry = f"{timestamp} | {latest_signal} | Entry: {last_close} | SL: {sl} | TP: {tp} | OFI: {ofi}\n"
    
    with open("manual_trades_log.txt", "a") as f:
        f.write(txt_entry)

    row = [timestamp, latest_signal, last_close, sl, tp, ofi, risk_pct, round(risk_amt, 2), position_size]
    import csv
    file = "trade_log.csv"
    if not os.path.exists(file):
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Signal", "Entry", "SL", "TP", "OFI", "Risk%", "Risk($)", "PositionSize"])
    with open(file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    st.success("✅ Trade saved to trade_log.csv and manual log")

# ========== LAST TIMESTAMP ==========
st.caption(f"⏱️ Updated: {datetime.now().strftime('%H:%M:%S')}")

# ========== PAGE AUTORELOAD ==========
st_autorefresh = st.empty()
st_autorefresh.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)
