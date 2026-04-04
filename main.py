import asyncio
from datetime import datetime
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
# URLs a revisar
# ===============================
sitios = [
    "https://www.flashscore.com/football/",
    "https://www.sofascore.com/football",
    "https://www.besoccer.com/live"
]

# ===============================
# Extraer partidos con Playwright
# ===============================
async def extraer_partidos(playwright, url):
    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # Espera que cargue JS
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        partidos = []

        # Selector genérico: ajustar según sitio
        for match in soup.select(".event__match, .live-match, .match-row"):
            equipos = match.select(".event__participant, .team-name")
            equipos_texto = " vs ".join([e.text.strip() for e in equipos]) if equipos else "Desconocido"
            resultado = match.select_one(".event__scores, .score")
            resultado_texto = resultado.text.strip() if resultado else "-"
            corner = match.select_one(".event__corners")
            corner_texto = corner.text.strip() if corner else "0"
            # Minuto aproximado
            minuto = match.select_one(".event__time, .minute")
            minuto_num = int(minuto.text.strip().replace("'", "").replace("ET","0")) if minuto else 0

            partidos.append({
                "equipos": equipos_texto,
                "resultado": resultado_texto,
                "corner": corner_texto,
                "minuto": minuto_num,
                "url": url
            })
        await browser.close()
        return partidos
    except Exception as e:
        print(f"Error al leer {url}: {e}")
        return []

# ===============================
# Reglas inteligentes
# ===============================
def aplicar_reglas(partidos):
    alertas = []
    # Agrupar por liga o grupo por ejemplo por primer equipo
    grupos = {}
    for p in partidos:
        key = p["equipos"].split(" ")[0]  # Ajusta si quieres otra forma
        grupos.setdefault(key, []).append(p)

    for group, games in grupos.items():
        empates = sum(1 for g in games if "0-0" in g["resultado"])
        favoritos_ganan = sum(1 for g in games if "-" in g["resultado"] and int(g["resultado"].split("-")[0]) > int(g["resultado"].split("-")[1]))
        no_favoritos_ganan = sum(1 for g in games if "-" in g["resultado"] and int(g["resultado"].split("-")[1]) > int(g["resultado"].split("-")[0]))

        # Regla 1: varios empates → apostar siguiente favorito
        if empates >= 2:
            alertas.append(f"{group}: Varios empates → Apostar al favorito siguiente")

        # Regla 2: nadie marca ambos → probable BTTS
        if all("0-0" in g["resultado"] for g in games):
            alertas.append(f"{group}: Nadie marca ambos → Probable BTTS")

        # Regla 3: favorito va perdiendo + minuto >= 35
        for g in games:
            if g["minuto"] >= 35 and "-" in g["resultado"]:
                local, away = map(int, g["resultado"].split("-"))
                if local < away:
                    alertas.append(f"{g['equipos']} → Favorito va perdiendo minuto {g['minuto']}")

        # Regla 4: corners info
        for g in games:
            if g["corner"] != "0":
                alertas.append(f"{g['equipos']} | Corners: {g['corner']}")

    return alertas

# ===============================
# Enviar alertas únicas
# ===============================
def enviar_alertas(alertas):
    seen = set()
    for a in alertas:
        if a not in seen:
            bot.send_message(chat_id=CHAT_ID, text=a)
            print("Enviado:", a)
            seen.add(a)

# ===============================
# Función principal
# ===============================
async def main():
    async with async_playwright() as p:
        tareas = [extraer_partidos(p, url) for url in sitios]
        resultados = await asyncio.gather(*tareas)
        partidos = [p for sub in resultados for p in sub]  # Aplanar lista
        alertas = aplicar_reglas(partidos)
        enviar_alertas(alertas)

if __name__ == "__main__":
    asyncio.run(main())
