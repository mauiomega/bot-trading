# === IMPORTACIONES Y LIBRERÍAS ===
import subprocess
import sys

def instalar_libreria(nombre):
    print(f"📦 Instalando {nombre}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", nombre])

try:
    import ta
except ImportError:
    instalar_libreria("ta")
    import ta

try:
    from twilio.rest import Client
except ImportError:
    instalar_libreria("twilio")
    from twilio.rest import Client

try:
    import pandas as pd
except ImportError:
    instalar_libreria("pandas")
    import pandas as pd

try:
    import requests
except ImportError:
    instalar_libreria("requests")
    import requests

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import os

# === KEEP ALIVE / FLASK ===
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    print(f"📡 Ping recibido - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "✅ Bot activo y funcionando 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# === CONFIGURACIÓN ===
EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
CLAVE_APP = os.getenv("CLAVE_APP")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_TOKEN")
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_WHATSAPP_TO = "whatsapp:+56974964168"

# === FUNCIONES DE DATOS ===
def obtener_tasa_cambio_usd_clp():
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=CLP"
        r = requests.get(url)
        r.raise_for_status()
        return r.json().get("rates", {}).get("CLP")
    except Exception as e:
        print(f"❌ Error USD/CLP: {e}")
        return None

def obtener_precio_btc_clp_buda():
    try:
        url = "https://www.buda.com/api/v2/markets/btc-clp/ticker"
        r = requests.get(url)
        r.raise_for_status()
        precio_str = r.json().get("ticker", {}).get("last_price", [None])[0]
        return float(precio_str) if precio_str else None
    except Exception as e:
        print(f"❌ Error Buda: {e}")
        return None

def obtener_datos_coingecko(dias=30):
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {"vs_currency": "clp", "days": dias}
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if "prices" not in data:
            print("❌ CoinGecko sin precios:", data)
            return None

        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df["Open"] = df["price"]
        df["High"] = df["price"]
        df["Low"] = df["price"]
        df["Close"] = df["price"]
        df["Volume"] = 0

        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['EMA9'] = ta.trend.ema_indicator(df['Close'], window=9)
        df['EMA21'] = ta.trend.ema_indicator(df['Close'], window=21)
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_high'] = bb.bollinger_hband()
        df['BB_low'] = bb.bollinger_lband()
        df['BB_mid'] = bb.bollinger_mavg()
        adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx.adx()
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['Stoch_k'] = stoch.stoch()
        df['Stoch_d'] = stoch.stoch_signal()
        return df
    except Exception as e:
        print(f"❌ Error CoinGecko: {e}")
        return None

# === FUNCIONES DE ANÁLISIS ===
def calcular_senal(df):
    if df is None or df.empty:
        return "ESPERAR", "Datos insuficientes"

    ultima = df.iloc[-1]
    señales_compra = 0
    señales_venta = 0

    if ultima['RSI'] < 30:
        señales_compra += 1
    elif ultima['RSI'] > 70:
        señales_venta += 1

    if ultima['MACD'] > ultima['MACD_signal']:
        señales_compra += 1
    elif ultima['MACD'] < ultima['MACD_signal']:
        señales_venta += 1

    if ultima['EMA9'] > ultima['EMA21']:
        señales_compra += 1
    elif ultima['EMA9'] < ultima['EMA21']:
        señales_venta += 1

    if ultima['Close'] < ultima['BB_low']:
        señales_compra += 1
    elif ultima['Close'] > ultima['BB_high']:
        señales_venta += 1

    if ultima['ADX'] > 25:
        señales_compra += 1
        señales_venta += 1

    if ultima['Stoch_k'] < 20 and ultima['Stoch_d'] < 20:
        señales_compra += 1
    elif ultima['Stoch_k'] > 80 and ultima['Stoch_d'] > 80:
        señales_venta += 1

    if señales_compra >= 4:
        return "COMPRAR", f"{señales_compra} indicadores apuntan a compra"
    elif señales_venta >= 4:
        return "VENDER", f"{señales_venta} indicadores apuntan a venta"
    else:
        return "ESPERAR", "No hay suficiente confirmación para actuar"

def calcular_rentabilidad_24h(df):
    if df is None or len(df) < 25:
        return None
    return (df.iloc[-1]['Close'] - df.iloc[-25]['Close']) / df.iloc[-25]['Close'] * 100

# === FUNCIONES DE ALERTA ===
def enviar_correo(asunto, mensaje):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, CLAVE_APP)
        server.send_message(msg)
        server.quit()
        print("✅ Correo enviado.")
    except Exception as e:
        print(f"❌ Error correo: {e}")

def enviar_whatsapp(mensaje):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        message = client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_FROM,
            to=TWILIO_WHATSAPP_TO
        )
        print("✅ WhatsApp enviado:", message.sid)
    except Exception as e:
        print(f"❌ Error WhatsApp: {e}")

def guardar_ultima_senal(senal, archivo="ultima_senal.txt"):
    try:
        with open(archivo, "w") as f:
            f.write(senal)
    except Exception as e:
        print(f"❌ Error guardar señal: {e}")

def leer_ultima_senal(archivo="ultima_senal.txt"):
    try:
        with open(archivo, "r") as f:
            return f.read().strip()
    except:
        return None

def generar_mensaje(df, senal, razon, rentabilidad, precio_btc_clp_buda=None):
    ultima = df.iloc[-1]
    close = ultima['Close']
    resumen = f"📈 Señal: {senal}\n"
    resumen += f"🕒 Fecha: {ultima.name.strftime('%Y-%m-%d %H:%M')}\n"
    resumen += f"💬 Motivo: {razon}\n"
    resumen += f"💰 Precio estimado: {close:,.2f} CLP\n"
    resumen += f"💸 Precio en Buda: {precio_btc_clp_buda:,.0f} CLP\n" if precio_btc_clp_buda else "💸 Precio en Buda: No disponible\n"
    resumen += (
        f"📊 RSI: {ultima['RSI']:.2f} | EMA9: {ultima['EMA9']:.2f} | EMA21: {ultima['EMA21']:.2f}\n"
        f"MACD: {ultima['MACD']:.2f} / Señal: {ultima['MACD_signal']:.2f}\n"
        f"Bandas BB: {ultima['BB_low']:.2f} - {ultima['BB_mid']:.2f} - {ultima['BB_high']:.2f}\n"
        f"ADX: {ultima['ADX']:.2f}\n"
        f"Estocástico: K={ultima['Stoch_k']:.2f} | D={ultima['Stoch_d']:.2f}\n"
    )
    resumen += f"\n🔄 Rentabilidad 24h: {rentabilidad:.2f}%\n" if rentabilidad else "\n🔄 Rentabilidad 24h: No disponible\n"
    resumen += "\n💬 Recomendación basada en análisis técnico automatizado.\n"
    return resumen

# === FUNCIÓN PRINCIPAL ===
def main():
    print(f"🕒 Ejecutando bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    precio_buda = obtener_precio_btc_clp_buda()
    df = obtener_datos_coingecko()
    if df is None:
        print("❌ Datos no disponibles.")
        return
    senal, razon = calcular_senal(df)
    rentabilidad = calcular_rentabilidad_24h(df)
    mensaje = generar_mensaje(df, senal, razon, rentabilidad, precio_buda)
    ultima = leer_ultima_senal()
    if senal != ultima:
        print("📬 Enviando nueva alerta...")
        enviar_correo(f"📈 Alerta BTC/CLP - {senal}", mensaje)
        enviar_whatsapp(mensaje)
        guardar_ultima_senal(senal)
    else:
        print("ℹ️ Sin cambios. No se envía alerta.")
    print(mensaje)

# === INICIO DE EJECUCIÓN ===
if __name__ == "__main__":
    print("🚀 Iniciando bot y servidor Flask...")
    keep_alive()
    while True:
        try:
            main()
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        print("⏳ Esperando 1 hora...\n")
        time.sleep(3600)
