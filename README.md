
# 🤖 Bot de Trading BTC/CLP

Este bot analiza el par **BTC/CLP** cada hora utilizando el indicador **RSI (Relative Strength Index)** y envía alertas por **WhatsApp** mediante **Twilio**. Está diseñado para ejecutarse 24/7 en la nube utilizando **Render**, gracias a un pequeño servidor web con **Flask** que evita la suspensión por inactividad.

---

## 🚀 ¿Qué hace este bot?

- Descarga datos del par **BTC/CLP** cada hora usando `yfinance`.
- Calcula el RSI con la librería `ta`.
- Si el RSI está por debajo de 25 → **posible compra**.
- Si el RSI está por encima de 70 → **posible venta**.
- Envía una **alerta automática por WhatsApp** usando `Twilio`.
- Se mantiene **activo 24/7** gracias a un servidor Flask para Render.

---

## 📦 Requisitos

Asegúrate de tener Python instalado. Luego ejecuta:

```bash
pip install -r requirements.txt
```

---

## 📁 Estructura del Proyecto

```plaintext
bot-trading/
├── main.py              # Código principal del bot y servidor Flask
├── requirements.txt     # Librerías necesarias
└── README.md            # Este archivo
```

---

## ⚙️ Configuración Twilio

1. Crea una cuenta en [https://www.twilio.com/](https://www.twilio.com/)
2. Activa el sandbox para WhatsApp.
3. Sustituye en `main.py` tus credenciales:

```python
TWILIO_SID = "TU_SID"
TWILIO_AUTH_TOKEN = "TU_TOKEN"
TWILIO_PHONE = "whatsapp:+14155238886"   # Número Twilio
MY_PHONE = "whatsapp:+569XXXXXXX"        # Tu número
```

---

## 💻 Ejecutar localmente

```bash
python main.py
```

El bot empezará a analizar el mercado cada hora y se mantendrá corriendo. También podrás acceder en tu navegador a [http://localhost:8080](http://localhost:8080).

---

## ☁️ Despliegue en Render (gratuito)

1. Sube este repositorio a GitHub.
2. Ve a [https://render.com/](https://render.com/), inicia sesión con GitHub.
3. Crea un **Web Service**:
   - Elige tu repo.
   - Branch: `main`
   - Build Command: *(déjalo vacío)*
   - Start Command:
     ```bash
     python main.py
     ```
   - Environment: `Python`
   - Free plan ✅
4. ¡Y listo! El bot se ejecutará 24/7 en la nube.

---

## 📞 Contacto

Para dudas, mejoras o colaboración, puedes contactar a [mauricioleal.c@gmail.com](mailto:mauricioleal.c@gmail.com)

---

## 🧠 Tecnologías utilizadas

- Python 🐍
- yfinance
- pandas
- ta (technical analysis)
- Flask
- Twilio (WhatsApp)
- schedule
- Render (deploy gratuito)

---
