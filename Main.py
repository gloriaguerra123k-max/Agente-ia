import requests

def get_data():
    url = "https://d.flashscore.com/x/feed/f_1_0_0_en_1"
    headers = {"x-fsign": "SW9D1eZo"}
    r = requests.get(url, headers=headers)
    return r.text

def analyze(data):
    alerts = []

    # 🟥 tarjetas rojas
    if "RC" in data:
        alerts.append("🟥 Roja detectada → partido cambia")

    # ⚽ corners
    corners = data.count("CORNER")
    if corners >= 8:
        alerts.append(f"⚽ {corners} corners → presión alta")

    # 🔥 ataques
    attacks = data.count("ATTACK")
    if attacks >= 25:
        alerts.append("🔥 Ataques constantes → gol probable")

    # ⏱️ minutos avanzados
    if "2nd Half" in data and attacks > 15:
        alerts.append("⏱️ Segunda parte activa → peligro de gol")

    return alerts

def send_telegram(msg):
    TOKEN = "AQUI_TU_TOKEN"
    CHAT_ID = "AQUI_TU_CHAT_ID"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

data = get_data()
alerts = analyze(data)

for alert in alerts:
    send_telegram(alert)
