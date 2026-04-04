import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime

# 🔹 Telegram
BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

def send_telegram(msg):
    """Envía mensaje por Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

async def scrape_site(page, url):
    """Scrapea una web y devuelve el HTML"""
    await page.goto(url)
    await page.wait_for_timeout(5000)
    return await page.content()

async def parse_flashscore(html):
    """Ejemplo Flashscore parse"""
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    for m in soup.select(".event__match"):
        try:
            teams = m.select(".event__participant")
            score = m.select_one(".event__scores")
            minute = m.select_one(".event__time")
            corners = m.select_one(".event__corners")  # si hay clase

            if not teams or not score:
                continue

            local = teams[0].text.strip()
            away = teams[1].text.strip()
            result = score.text.strip()
            min_txt = minute.text.strip() if minute else "0"
            minute_num = int(min_txt.replace("'", "").replace("ET", "0"))

            corners_num = int(corners.text.strip()) if corners else 0

            matches.append({
                "site": "Flashscore",
                "local": local,
                "away": away,
                "score": result,
                "minute": minute_num,
                "corners": corners_num
            })
        except:
            continue
    return matches

async def parse_sofascore(html):
    """Ejemplo Sofascore parse"""
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    # Ajustar selectores según Sofascore
    for m in soup.select(".event-row"):
        try:
            teams = m.select(".team-name")
            score = m.select_one(".score")
            minute = m.select_one(".minute")
            corners = m.select_one(".corners")

            if not teams or not score:
                continue

            local = teams[0].text.strip()
            away = teams[1].text.strip()
            result = score.text.strip()
            minute_num = int(minute.text.strip().replace("'", "")) if minute else 0
            corners_num = int(corners.text.strip()) if corners else 0

            matches.append({
                "site": "Sofascore",
                "local": local,
                "away": away,
                "score": result,
                "minute": minute_num,
                "corners": corners_num
            })
        except:
            continue
    return matches

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        urls = {
            "Flashscore": "https://www.flashscore.com/football/",
            "Sofascore": "https://www.sofascore.com/football",
            "BeSoccer": "https://www.besoccer.com/live"
        }

        all_matches = []

        for site, url in urls.items():
            try:
                html = await scrape_site(page, url)
                if "Flashscore" in site:
                    all_matches.extend(await parse_flashscore(html))
                elif "Sofascore" in site:
                    all_matches.extend(await parse_sofascore(html))
                else:
                    # BeSoccer, parse similar a Flashscore
                    all_matches.extend(await parse_flashscore(html))
            except Exception as e:
                print(f"Error scraping {site}: {e}")

        # --- Reglas de apuestas inteligentes ---
        alertas = []
        leagues = {}
        for m in all_matches:
            # Agrupamos por liga/grupo ficticio usando el nombre del equipo
            key = m["local"].split(" ")[0]
            leagues.setdefault(key, []).append(m)

        for group, games in leagues.items():
            empates = sum(1 for g in games if "0-0" in g["score"])
            favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[0]) > int(g["score"].split("-")[1]))
            no_favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[1]) > int(g["score"].split("-")[0]))

            # 1️⃣ Regla: varios empates → apostar siguiente favorito
            if empates >= 2:
                alertas.append(f"{group}: Varios empates → Apostar al favorito siguiente")

            # 2️⃣ Regla: todos 0-0 → probable ambos marcan
            if all("0-0" in g["score"] for g in games):
                alertas.append(f"{group}: Nadie marca ambos → Probable BTTS")

            # 3️⃣ Favorito va perdiendo y minuto >= 35
            for g in games:
                try:
                    local_score, away_score = map(int, g["score"].split("-"))
                    if g["minute"] >= 35 and local_score < away_score:
                        alertas.append(f"{g['local']} vs {g['away']} → Favorito va perdiendo minuto {g['minute']}")
                except:
                    continue

            # 4️⃣ Reglas de tiros de esquina
            for g in games:
                if g["corners"] >= 5:
                    alertas.append(f"{g['local']} vs {g['away']} → Muchos corners: {g['corners']}")

        # Enviar alertas únicas
        seen = set()
        for alert in alertas:
            if alert not in seen:
                send_telegram(alert)
                seen.add(alert)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
