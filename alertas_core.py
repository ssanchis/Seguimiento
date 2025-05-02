# alertas_core.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# CONFIGURACIÓN
TICKERS = ["AAPL", "MSFT","JNJ","REP.MC", "PG", "KO","O","CVX","TTE"]
ALERTA_UMBRAL = 0.98
EMAIL_ALERTA = "ssanchiscasco@gmail.com"
EMAIL_CONTRASENA = "icxn wgnh dmfx ztim"

def descargar_datos():
    data_historico = {}
    data_reciente = {}

    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)

            # Descargar histórico diario
            hist = stock.history(period="max", interval="1d")

            if not isinstance(hist.index, pd.DatetimeIndex):
                hist.index = pd.to_datetime(hist.index)

            hist = hist.reset_index()  # Ahora "Date" es una columna
            hist["Date"] = pd.to_datetime(hist["Date"])
            hist.set_index("Date", inplace=True)
            data_historico[ticker] = hist

            # Reciente horario
            reciente = stock.history(period="2y", interval="1h")

            # Verifica si el índice es DateTimeIndex (debería serlo)
            if not isinstance(reciente.index, pd.DatetimeIndex):
                print(f"⚠️ El índice no es datetime para {ticker}, intentando corregir...")

            # Ahora convertimos el índice a una columna llamada "Date"
            reciente = reciente.reset_index()

            # Aseguramos que la columna "Datetime" esté bien
            if "Datetime" in reciente.columns:
                reciente["Date"] = pd.to_datetime(reciente["Datetime"])
                reciente.drop(columns=["Datetime"], inplace=True)
            else:
                reciente["Date"] = pd.to_datetime(reciente["Date"] if "Date" in reciente else reciente.index)

            reciente.set_index("Date", inplace=True)
            data_reciente[ticker] = reciente

        except Exception as e:
            print(f"❌ Error con {ticker}: {e}")
            continue

    return data_historico, data_reciente

def enviar_alerta(mensaje):
    try:
        msg = MIMEText(str(mensaje), _charset="utf-8")
        msg["Subject"] = "🔔 Alerta de Mercado"
        msg["From"] = EMAIL_ALERTA
        msg["To"] = EMAIL_ALERTA

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ALERTA, EMAIL_CONTRASENA)
            server.send_message(msg)
        print(f"✅ Correo enviado: {mensaje}")
    except Exception as e:
        print(f"Error enviando correo: {e}")

def check_alertas(datos_historicos, datos_recientes):
    alertas = []
    hoy = datetime.now()

    for ticker in datos_historicos.keys():
        # Datos históricos
        hist = datos_historicos[ticker]
        hist.index = pd.to_datetime(hist.index).tz_localize(None)

        # Datos recientes (el índice ya es de tipo Datetime)
        reciente = datos_recientes[ticker]
        reciente.index = pd.to_datetime(reciente.index).tz_localize(None)

        # Lo que sigue depende de cómo estén estructurados los datos
        precio_actual = reciente["Close"].iloc[-1]
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        reciente_2y = reciente[reciente.index >= hoy - timedelta(days=730)]
        max_2y = reciente_2y["High"].max() if not reciente_2y.empty else None
        min_2y = reciente_2y["Low"].min() if not reciente_2y.empty else None

        reciente_1y = reciente[reciente.index >= hoy - timedelta(days=365)]
        max_1y = reciente_1y["High"].max() if not reciente_1y.empty else None
        min_1y = reciente_1y["Low"].min() if not reciente_1y.empty else None

        def alerta(mensaje):
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        if precio_actual >= max_historico * ALERTA_UMBRAL:
            alerta(f"🔔 {ticker} cerca de su MÁXIMO histórico ({precio_actual:.2f} vs {max_historico:.2f})")
        if precio_actual <= min_historico * (2 - ALERTA_UMBRAL):
            alerta(f"🔔 {ticker} cerca de su MÍNIMO histórico ({precio_actual:.2f} vs {min_historico:.2f})")
        if max_1y and precio_actual >= max_1y * ALERTA_UMBRAL:
            alerta(f"📈 {ticker} cerca de su MÁXIMO de 1 año ({precio_actual:.2f} vs {max_1y:.2f})")
        if min_1y and precio_actual <= min_1y * (2 - ALERTA_UMBRAL):
            alerta(f"📉 {ticker} cerca de su MÍNIMO de 1 año ({precio_actual:.2f} vs {min_1y:.2f})")
        if max_2y and precio_actual >= max_2y * ALERTA_UMBRAL:
            alerta(f"📈 {ticker} cerca de su MÁXIMO de 2 años ({precio_actual:.2f} vs {max_2y:.2f})")
        if min_2y and precio_actual <= min_2y * (2 - ALERTA_UMBRAL):
            alerta(f"📉 {ticker} cerca de su MÍNIMO de 2 años ({precio_actual:.2f} vs {min_2y:.2f})")

    return alertas


