# dashboard_empresas.py

import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
import schedule
import time
import threading

st.set_page_config(page_title="Dashboard Empresas", layout="wide")

# ------------------------------------------
# CONFIGURACIÓN
PASSWORD = "soyrica"  # Cambia aquí tu contraseña
TICKERS = ["AAPL", "MSFT", "GOOGL"]  # Empresas que quieres seguir
ALERTA_UMBRAL = 0.98  # 98% del máximo o 102% del mínimo
EMAIL_ALERTA = "ssanchiscasco@gmail.com"  # Cambia aquí tu correo para recibir alertas
EMAIL_CONTRASENA = "ssanchis105567"  # Tu contraseña de correo
# ------------------------------------------

# Función para descargar datos
@st.cache_data(ttl=43200)  # cachea 12h = 43200 segundos
def descargar_datos():
    data = {}
    for ticker in TICKERS:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="max")
        data[ticker] = hist
    return data

# Función para enviar alerta por correo
def enviar_alerta(mensaje):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ALERTA, EMAIL_CONTRASENA)
        server.sendmail(EMAIL_ALERTA, EMAIL_ALERTA, mensaje)
        server.quit()
        print(f"Correo enviado: {mensaje}")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

# Función para chequear alertas
def check_alertas(data):
    alertas = []
    for ticker, hist in data.items():
        precio_actual = hist["Close"].iloc[-1]
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()
        if precio_actual >= max_historico * ALERTA_UMBRAL:
            mensaje = f"🔔 {ticker} está cerca de su MÁXIMO histórico ({precio_actual:.2f} vs {max_historico:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)
        if precio_actual <= min_historico * (2 - ALERTA_UMBRAL):
            mensaje = f"🔔 {ticker} está cerca de su MÍNIMO histórico ({precio_actual:.2f} vs {min_historico:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)
    return alertas

# Sistema de contraseña
password = st.text_input("🔒 Introduce la contraseña para acceder:", type="password")
if password != PASSWORD:
    st.warning("Contraseña incorrecta o falta de contraseña.")
    st.stop()

# Dashboard principal
st.title("📊 Seguimiento de Empresas")

data = descargar_datos()

# Una pestaña por empresa
tabs = st.tabs([f"🏢 {ticker}" for ticker in TICKERS])

for i, ticker in enumerate(TICKERS):
    with tabs[i]:
        st.subheader(f"Datos de {ticker}")

        hist = data[ticker]
        precio_actual = hist["Close"].iloc[-1]
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        # KPIs en fila
        col1, col2, col3 = st.columns(3)
        col1.metric("📈 Máximo histórico", f"${max_historico:.2f}")
        col2.metric("📉 Mínimo histórico", f"${min_historico:.2f}")
        col3.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico histórico debajo
        st.markdown("### 📊 Evolución histórica del precio")
        st.line_chart(hist["Close"])

