import asyncio
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ===============================
# Configuración del bot Telegram
# ===============================
BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===============================
# Sitios a escanear
# ===============================
URLS = [
    "https://www.flashscore.com/football/",
    "https://www.sofascore.com/football",
    "https://www.besoccer.com/live"
]

# ===============================
# Función para extraer partidos
# ===============================
async def scrape_site(page, url):
    try:
        await page.goto(url)
        await page.wait_for_timeout(5000)  # Espera 5 seg para que cargue todo
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        matches = []

        # Ejemplo genérico, ajustar según estructura real
        for m in soup.select(".event__match, .live-match, .match-row"):
            equipos = m.select(".event__participant, .team-name")
            resultado = m.select_one(".event__scores, .score")
            corner = m.select_one(".event__corners")

            if not equipos or not resultado:
                continue

            local = equipos[0].text.strip()
            away = equipos[1].text.strip()
            score = resultado.text.strip()
            corner_txt = corner.text.strip() if corner else "0"

            # Extraer minuto si está
            minute_tag = m.select_one(".event__time, .minute")
            minute_txt = minute_tag.text.strip() if minute_tag else "0"
            try:
                minute_num = int(minute_txt.replace("'", "").replace("ET", "0"))
            except:
                minute_num = 0

            matches.append({
                "site": url,
                "local": local,
                "away": away,
                "score": score,
                "minute": minute_num,
                "corners": corner_txt
            })
        return matches
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# ===============================
# Función para aplicar reglas
# ===============================
def aplicar_reglas(matches):
    alertas = []
    # Agrupar por liga/grupo (ejemplo usando primer equipo)
    grupos = {}
    for m in matches:
        key = m["local"].split(" ")[0]
        grupos.setdefault(key, []).append(m)

    for grupo, juegos in grupos.items():
        empates = sum(1 for g in juegos if "0-0" in g["score"])
        favoritos_ganan = sum(1 for g in juegos if int(g["score"].split("-")[0]) > int(g["score"].split("-")[1]))
        no_favoritos_ganan = sum(1 for g in juegos if int(g["score"].split("-")[1]) > int(g["score"].split("-")[0]))

        # Reglas
        if empates >= 2:
            alertas.append(f"{grupo}: Varios empates → Apostar al favorito siguiente")

        if all("0-0" in g["score"] for g in juegos):
            alertas.append(f"{grupo}: Nadie marca ambos → Probable BTTS")

        for g in juegos:
            if g["minute"] >= 35 and int(g["score"].split("-")[0]) < int(g["score"].split("-")[1]):
                alertas.append(f"{g['local']} vs {g['away']} → Favorito va perdiendo minuto {g['minute']} | Corners: {g['corners']}")

    return alertas

# ===============================
# Función principal
# ===============================
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        all_matches = []
        for url in URLS:
            matches = await scrape_site(page, url)
            all_matches.extend(matches)

        alertas = aplicar_reglas(all_matches)

        # Enviar alertas únicas
        seen = set()
        for alert in alertas:
            if alert not in seen:
                send_telegram(alert)
                print("Enviado:", alert)
                seen.add(alert)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
