import requests

TELEGRAM_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def obtener_partidos():
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    r = requests.get(url)
    return r.json()

def analizar():
    data = obtener_partidos()
    eventos = data.get("events", [])

    empates = 0
    alertas = []

    for e in eventos:
        comp = e["competitions"][0]
        equipos = comp["competitors"]

        local = equipos[0]["team"]["name"]
        visitante = equipos[1]["team"]["name"]

        goles_local = int(equipos[0]["score"])
        goles_visitante = int(equipos[1]["score"])

        estado = comp["status"]["type"]["description"]
        minuto = comp["status"].get("displayClock", "0")

        # Detectar empate
        if goles_local == goles_visitante:
            empates += 1

        # Regla tuya: empate + minuto alto
        if goles_local == goles_visitante:
            try:
                min_num = int(minuto.split(":")[0])
                if min_num >= 70:
                    alertas.append(f"🔥 {local} vs {visitante} → posible GOL")
            except:
                pass

    # Regla: muchos empates
    if empates >= 2:
        alertas.append("⚽ Hay varios empates → apostar siguiente partido")

    return alertas

def main():
    alertas = analizar()

    if alertas:
        for a in alertas:
            enviar_telegram(a)
    else:
        enviar_telegram("🤖 Sin señales fuertes ahora")

if __name__ == "__main__":
    main()
