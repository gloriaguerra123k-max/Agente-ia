import asyncio
import requests
from playwright.async_api import async_playwright
from datetime import datetime

BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

async def scrape_site(page, url):
    await page.goto(url)
    await page.wait_for_timeout(5000)
    content = await page.content()
    return content

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()

        # 🔹 Sitios a escanear (puedes agregar más)
        urls = [
            "https://www.flashscore.com/football/",
            "https://www.sofascore.com/football",
            "https://www.besoccer.com/live"
        ]

        all_matches = []

        for url in urls:
            try:
                html = await scrape_site(page, url)
                # Hacemos parse básico de partidos
                # Ajustar según estructura real de cada sitio
                matches = []
                soup = BeautifulSoup(html, "html.parser")

                # Ejemplo para Flashscore
                for m in soup.select(".event__match"):
                    minute = m.select_one(".event__time")
                    teams = m.select(".event__participant")
                    score = m.select_one(".event__scores")

                    if not teams or not score:
                        continue

                    local = teams[0].text.strip()
                    away = teams[1].text.strip()
                    result = score.text.strip()
                    min_txt = minute.text.strip() if minute else "0"
                    minute_num = int(min_txt.replace("'", "").replace("ET", "0"))

                    matches.append({
                        "site": url,
                        "local": local,
                        "away": away,
                        "score": result,
                        "minute": minute_num
                    })
                all_matches.extend(matches)

            except Exception as e:
                print("Error scraping", url, e)

        # --- Aplicar tus reglas inteligentes ---
        leagues = {}
        for m in all_matches:
            key = m["local"].split(" ")[0]  # group by team base or league
            leagues.setdefault(key, []).append(m)

        alertas = []
        for group, games in leagues.items():

            empates = sum(1 for g in games if "0-0" in g["score"])
            favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[0]) > int(g["score"].split("-")[1]))
            no_favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[1]) > int(g["score"].split("-")[0])

            # Regla 1: varios empates → apostar siguiente favorito
            if empates >= 2:
                alertas.append(f"{group}: Varios empates → Apostar al favorito siguiente")

            # Regla 2: nadie marca ambos → probable BTTS
            if all("0-0" in g["score"] for g in games):
                alertas.append(f"{group}: Nadie marca ambos → Probable BTTS")

            # Regla favorito va perdiendo + minuto > 35
            for g in games:
                if g["minute"] >= 35 and int(g["score"].split("-")[0]) < int(g["score"].split("-")[1]):
                    alertas.append(f"{g['local']} vs {g['away']} → Favorito va perdiendo minuto {g['minute']}")

        # Enviar alertas únicas
        seen = set()
        for alert in alertas:
            if alert not in seen:
                send_telegram(alert)
                seen.add(alert)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
