import requests

BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

def enviar(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

ligas = [
    "eng.1", "esp.1", "ger.1", "ita.1", "fra.1",
    "bra.1", "arg.1", "col.1", "mex.1"
]

def obtener_eventos():
    eventos = []
    for liga in ligas:
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r = requests.get(url)
            data = r.json()
            for e in data.get("events", []):
                e["liga"] = liga
                eventos.append(e)
        except:
            pass
    return eventos

def analizar():
    eventos = obtener_eventos()

    ligas_dict = {}

    # ORGANIZAR POR LIGA
    for e in eventos:
        liga = e["liga"]

        comp = e["competitions"][0]
        equipos = comp["competitors"]

        local = equipos[0]["team"]["name"]
        visitante = equipos[1]["team"]["name"]

        goles_local = int(equipos[0]["score"])
        goles_visitante = int(equipos[1]["score"])

        estado = comp["status"]["type"]["description"]
        minuto_txt = comp["status"].get("displayClock", "0")

        try:
            minuto = int(minuto_txt.split(":")[0])
        except:
            minuto = 0

        partido = {
            "local": local,
            "visitante": visitante,
            "goles_local": goles_local,
            "goles_visitante": goles_visitante,
            "minuto": minuto,
            "estado": estado
        }

        if liga not in ligas_dict:
            ligas_dict[liga] = []

        ligas_dict[liga].append(partido)

    alertas = []

    # 🔥 TUS REGLAS
    for liga, partidos in ligas_dict.items():

        empates = 0
        no_favoritos_ganando = 0

        for p in partidos:

            # empate
            if p["goles_local"] == p["goles_visitante"]:
                empates += 1

            # minuto alto empate
            if p["goles_local"] == p["goles_visitante"] and p["minuto"] >= 70:
                alertas.append(
                    f"🔥 {p['local']} vs {p['visitante']} ({liga}) → POSIBLE GOL MIN {p['minuto']}"
                )

            # detectar “raro” (simulación no favorito ganando)
            if p["goles_local"] != p["goles_visitante"]:
                no_favoritos_ganando += 1

        # regla: muchos empates → siguiente partido
        if empates >= 2:
            alertas.append(f"⚽ {liga} → MUCHOS EMPATES → apostar siguiente partido")

        # regla: patrón raro → favorito después
        if empates >= 1 and no_favoritos_ganando >= 1:
            alertas.append(f"🔥 {liga} → patrón raro → apostar FAVORITO siguiente")

        # regla: ningún ambos marcan
        ambos_marcan = 0
        for p in partidos:
            if p["goles_local"] > 0 and p["goles_visitante"] > 0:
                ambos_marcan += 1

        if ambos_marcan == 0 and len(partidos) >= 3:
            alertas.append(f"💣 {liga} → NADIE marca ambos → PROBABLE AMBOS MARCAN")

    return alertas

def main():
    alertas = analizar()

    if alertas:
        for a in alertas:
            enviar(a)
    else:
        enviar("🤖 Sin señales fuertes ahora")

if __name__ == "__main__":
    main()
