import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from telegram import Bot

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
    "https://www.soccerway.com/matches/",
    "https://www.besoccer.com/live"
]

# ===============================
# Extraer partidos de cada sitio
# ===============================
def extraer_partidos(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        
        partidos = []
        # Selector genérico, se puede ajustar para cada sitio
        for match in soup.select(".event__match, .live-match, .match-row"):
            equipos = match.select(".event__participant, .team-name")
            equipos_texto = " vs ".join([e.text.strip() for e in equipos]) if equipos else "Desconocido"
            
            resultado = match.select_one(".event__scores, .score") 
            resultado_texto = resultado.text.strip() if resultado else "-"
            
            corner = match.select_one(".event__corners")  
            corner_texto = corner.text.strip() if corner else "0"
            
            # Minuto del partido si existe
            minuto = match.select_one(".event__time, .minute")
            minuto_num = int(minuto.text.strip().replace("'", "").replace("ET", "0")) if minuto else 0

            partidos.append({
                "equipos": equipos_texto,
                "resultado": resultado_texto,
                "corner": corner_texto,
                "minuto": minuto_num
            })
        return partidos
    except Exception as e:
        print(f"Error al leer {url}: {e}")
        return []

# ===============================
# Aplicar reglas inteligentes
# ===============================
def aplicar_reglas(partido):
    equipos = partido["equipos"]
    resultado = partido["resultado"]
    corner = partido["corner"]
    minuto = partido["minuto"]
    alerta = ""

    # 1️⃣ Regla: empate 0-0 → ambos marcan probable
    if resultado == "0-0":
        alerta = "⚽ Ambos marcan probable (0-0)"
    
    # 2️⃣ Regla: varios empates → apostar siguiente favorito
    if "empate" in resultado.lower():
        alerta += " | ⚽ Muchos empates → apostar siguiente favorito"
    
    # 3️⃣ Regla: favorito va perdiendo + minuto >= 35
    if "favorito" in equipos.lower() and "va perdiendo" in resultado.lower() and minuto >= 35:
        alerta += " | ⚽ Apostar al favorito (cuota baja)"
    
    # 4️⃣ Info de corners
    if corner != "0":
        alerta += f" | Corners: {corner}"
    
    return alerta

# ===============================
# Función principal
# ===============================
def revisar_partidos():
    hoy = datetime.today().strftime("%d/%m/%Y")
    for sitio in sitios:
        partidos = extraer_partidos(sitio)
        for partido in partidos:
            alerta = aplicar_reglas(partido)
            if alerta:
                mensaje = f"{partido['equipos']} | {partido['resultado']} | {alerta}"
                bot.send_message(chat_id=CHAT_ID, text=mensaje)
                print("Enviado:", mensaje)

# ===============================
# Loop principal
# ===============================
if __name__ == "__main__":
    revisar_partidos()
