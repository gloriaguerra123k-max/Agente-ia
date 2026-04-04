import asyncio
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from playwright.async_api import async_playwright

# ===============================
# Configuración del bot Telegram
# ===============================
BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"
bot = Bot(token=BOT_TOKEN)

# ===============================
# Sitios a escanear (dinámicos)
# ===============================
urls = [
    "https://www.flashscore.com/football/",
    "https://www.sofascore.com/football",
    "https://www.besoccer.com/live"
]

# ===============================
# Función para enviar alertas
# ===============================
def enviar_telegram(msg):
    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        print("Enviado:", msg)
    except Exception as e:
        print("Error Telegram:", e)

# ===============================
# Función para parsear partidos
# ===============================
def parsear_partidos(html, site_url):
    soup = BeautifulSoup(html, "html.parser")
    partidos = []

    # Genérico: ajusta según sitio
    for match in soup.select(".event__match, .live-match, .match-row"):
        equipos = match.select(".event__participant, .team-name")
        resultado = match.select_one(".event__scores, .score")
        corner = match.select_one(".event__corners")

        if not equipos or not resultado:
            continue

        local = equipos[0].text.strip()
        away = equipos[1].text.strip() if len(equipos) > 1 else "Desconocido"
        score = resultado.text.strip()
        corners = corner.text.strip() if corner else "0"

        # Intentar sacar minuto si existe
        minuto_tag = match.select_one(".event__time")
        minuto = 0
        if minuto_tag:
            txt = minuto_tag.text.strip().replace("ET", "0").replace("'", "")
            try:
                minuto = int(txt)
            except:
                minuto = 0

        partidos.append({
            "site": site_url,
            "local": local,
            "away": away,
            "score": score,
            "minute": minuto,
            "corners": corners
        })
    return partidos

# ===============================
# Función para aplicar reglas inteligentes
# ===============================
def aplicar_reglas(partidos):
    alertas = []
    grupos = {}

    # Agrupar por liga/equipo base (puedes ajustar)
    for p in partidos:
        key = p["local"].split(" ")[0]
        grupos.setdefault(key, []).append(p)

    for group, games in grupos.items():
        empates = sum(1 for g in games if "0-0" in g["score"])
        favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[0]) > int(g["score"].split("-")[1]))
        no_favoritos_ganan = sum(1 for g in games if int(g["score"].split("-")[1]) > int(g["score"].split("-")[0]))

        # Regla 1: varios empates → apostar siguiente favorito
        if empates >= 2:
            alertas.append(f"{group}: ⚽ Varios empates → Apostar al favorito siguiente")

        # Regla 2: nadie marca ambos → probable BTTS
        if all("0-0" in g["score"] for g in games):
            alertas.append(f"{group}: ⚽ Nadie marca ambos → Probable BTTS")

        # Regla favorito va perdiendo + minuto > 35
        for g in games:
            if g["minute"] >= 35 and int(g["score"].split("-")[0]) < int(g["score"].split("-")[1]):
                alertas.append(f"{g['local']} vs {g['away']} → ⚽ Favorito va perdiendo minuto {g['minute']} | Corners: {g['corners']}")

    return list(set(alertas))

# ===============================
# Función principal con Playwright
# ===============================
async def main():
    all_partidos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in urls:
            try:
                await page.goto(url)
                await page.wait_for_timeout(8000)  # espera que cargue JS
                html = await page.content()
                partidos = parsear_partidos(html, url)
                all_partidos.extend(partidos)
            except Exception as e:
                print("Error cargando:", url, e)

        await browser.close()

    # Aplicar reglas y enviar alertas
    alertas = aplicar_reglas(all_partidos)
    for alerta in alertas:
        enviar_telegram(alerta)

# ===============================
# Ejecutar
# ===============================
if __name__ == "__main__":
    asyncio.run(main())
