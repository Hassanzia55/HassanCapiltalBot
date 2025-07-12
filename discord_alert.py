import requests
import json
import os

sent_last_signal = ""
def send_discord_alert(webhook_url, signal, entry, sl, tp, ofi, confidence, chart_image_path=None, dashboard_link=None):
    global sent_last_signal
    if signal == sent_last_signal or signal == "🟡 No Trade":
        print("🔁 No new signal to send.")
        return

    embed = {
        "title": f"📢 {signal}",
        "description": f"""**Entry**: `{entry}`
🛡️ **SL**: `{sl}` | 🎯 **TP**: `{tp}`
📊 **OFI**: `{ofi}` | ⚡ **Confidence**: `{confidence}`""",
        "color": 65300
    }

    payload_json = json.dumps({
        "username": "CryptoScalpBot 🤖",
        "content": "",
        "embeds": [embed]
    })

    if chart_image_path and os.path.exists(chart_image_path):
        with open(chart_image_path, "rb") as f:
            files = {"file": ("chart.png", f, "image/png")}
            response = requests.post(
                webhook_url,
                data={"payload_json": payload_json},
                files=files
            )
    else:
        response = requests.post(webhook_url, headers={'Content-Type': 'application/json'}, data=payload_json)

    if response.status_code in [200, 204]:
        print("✅ Discord alert sent.")
        sent_last_signal = signal
    else:
        print("❌ Discord send fail: ", response.text)