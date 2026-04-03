import requests

def get_data():
    url = "https://d.flashscore.com/x/feed/f_1_0_0_en_1"
    headers = {"x-fsign": "SW9D1eZo"}
    r = requests.get(url, headers=headers)
    return r.text

def parse_matches(data):
    lines = data.split("\n")
    leagues = {}
    current_league = "General"

    for line in lines:
        if "SA÷" in line:
            current_league = line.split("÷")[-1]
            leagues[current_league] = []

        if "AA÷" in line:
            parts = line.split("÷")
            match = {
                "raw": line,
                "score": line.count("¬")  # aproximación
            }
            leagues[current_league].append(match)

    return leagues

def analyze_league(name, matches):
    alerts = []

    total_matches = len(matches)

    if total_matches < 2:
        return alerts

    # Detectar empates (aproximado)
    draws = sum(1 for m in matches if "0¬0" in m["raw"])

    # Detectar pocos goles
    low_goals = sum(1 for m in matches if "1¬0" in m["raw"] or "0¬1" in m["raw"])

    # Regla 1: muchos empates → favorito siguiente
    if draws >= 2:
        alerts.append(f"📊 {name}: Muchos empates → apostar FAVORITO siguiente")

    # Regla 2: pocos goles → ambos marcan siguiente
    if low_goals >= 2:
        alerts.append(f"📊 {name}: Pocos goles → apostar AMBOS MARCAN")

    # Regla 3: mezcla rara (tu lógica)
    if draws >= 1 and low_goals >= 1:
        alerts.append(f"📊 {name}: Patrón mixto → buscar FAVORITO en vivo")

    # Regla 4: muchos partidos sin BTTS
    if total_matches >= 4 and low_goals >= 3:
        alerts.append(f"📊 {name}: Sin ambos marcan → apostar BTTS próximo")

    return alerts

def send_telegram(msg):
    TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
    CHAT_ID = "8642959008"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

data = get_data()
leagues = parse_matches(data)

all_alerts = []

for league, matches in leagues.items():
    alerts = analyze_league(league, matches)
    all_alerts.extend(alerts)

if not all_alerts:
    send_telegram("🤖 Sin patrones claros ahora")

for alert in all_alerts:
    send_telegram(alert)
