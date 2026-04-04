import asyncio
from playwright.async_api import async_playwright
import requests

# Tu Telegram Bot
BOT_TOKEN = "8736503875:AAFXmcNIudR1xGufKm7YbkZpLPCtLbq9scs"
CHAT_ID = "8642959008"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Función para enviar mensaje a Telegram
def send_telegram(message):
    requests.get(TELEGRAM_URL, params={"chat_id": CHAT_ID, "text": message})

# Función principal para analizar la página
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Cambia esta URL por la de los partidos que quieres leer
        await page.goto("https://www.flashscore.com/")
        await page.wait_for_timeout(5000)  # Espera 5 segundos a que cargue la página
        
        # Aquí deberías agregar la lógica para leer la página
        # Esto es un ejemplo básico
        partidos = await page.query_selector_all(".event__match")  # Cambia según la página
        mensajes = []

        for partido in partidos:
            texto = await partido.inner_text()
            if "0-0" in texto or "empate" in texto:
                mensajes.append(f"MUCHOS EMPATES -> apostar siguiente partido:\n{texto}")
            else:
                mensajes.append(f"Resultado observado:\n{texto}")
        
        # Envía los mensajes a Telegram
        for msg in mensajes:
            send_telegram(msg)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
