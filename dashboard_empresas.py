# dashboard_empresas.py

import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
import schedule
import time
import threading


# ------------------------------------------
# CONFIGURACIÓN
PASSWORD = "miclave123"  # Cambia aquí tu contraseña
TICKERS = ["AAPL", "MSFT", "GOOGL"]  # Empresas que quieres seguir
ALERTA_UMBRAL = 0.98  # 98% del máximo o 102% del mínimo
EMAIL_ALERTA = "tucorreo@gmail.com"  # Cambia aquí tu correo para recibir alertas
EMAIL_CONTRASENA = "tucontrasenaemail"  # Tu contraseña de correo
# ------------------------------------------

# Función para descargar datos
@st.cache_data(ttl=43200)  # cachea 12h = 43200 segundos
def descargar_datos():
    data = {}
    for ticker in TICKERS:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
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
st.title("📊 Dashboard Empresas")

data = descargar_datos()

tab1, tab2, tab3 = st.tabs(["📈 Precios", "📏 Máximos/Mínimos", "🚨 Alertas"])

with tab1:
    st.header("Precios actuales")
    for ticker in TICKERS:
        st.subheader(ticker)
        st.line_chart(data[ticker]["Close"])

with tab2:
    st.header("Máximos y mínimos históricos")
    for ticker in TICKERS:
        st.subheader(ticker)
        st.metric(label=f"{ticker} - Máximo", value=f"${data[ticker]['High'].max():.2f}")
        st.metric(label=f"{ticker} - Mínimo", value=f"${data[ticker]['Low'].min():.2f}")

with tab3:
    st.header("Alertas activas")
    alertas_activas = check_alertas(data)
    if alertas_activas:
        for alerta in alertas_activas:
            st.error(alerta)
    else:
        st.success("Sin alertas activas 🚀")

