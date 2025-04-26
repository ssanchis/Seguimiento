# dashboard_empresas.py

import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
import schedule
import time
import threading
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Empresas", layout="wide")

# ------------------------------------------
# CONFIGURACIÓN
PASSWORD = "soyrica"  # Cambia aquí tu contraseña
TICKERS = ["AAPL", "MSFT","JNJ","REP.MC", "PG", "KO","O","CVX","TTE"]  # Empresas que quieres seguir
ALERTA_UMBRAL = 0.98  # 98% del máximo o 102% del mínimo
EMAIL_ALERTA = "ssanchiscasco@gmail.com"  # Cambia aquí tu correo para recibir alertas
EMAIL_CONTRASENA = "ssanchis105567"  # Tu contraseña de correo
# ------------------------------------------

# Función para descargar datos
@st.cache_data(ttl=43200)  # cachea 12h = 43200 segundos
def descargar_datos():
    data = {}
    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max")
            if hist.empty:
                print(f"⚠️ Datos vacíos para {ticker}")
                continue
            hist = hist.reset_index()  # Pasa 'Date' a columna
            hist["Date"] = pd.to_datetime(hist["Date"])  # Asegura tipo datetime
            data[ticker] = hist
        except Exception as e:
            print(f"❌ Error descargando {ticker}: {e}")
            continue
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


def check_alertas(data):
    alertas = []
    hoy = datetime.now()

    for ticker, hist in data.items():
        # Asegurar que 'Date' esté en datetime y es el índice
        if 'Date' in hist.columns:
            hist.set_index('Date', inplace=True)
        hist.index = pd.to_datetime(hist.index)

        precio_actual = hist["Close"].iloc[-1]

        # Histórico total
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        # Último año
        hace_un_anyo = hoy - timedelta(days=365)
        hist_1y = hist.loc[hace_un_anyo:]
        if not hist_1y.empty:
            max_1y = hist_1y["High"].max()
            min_1y = hist_1y["Low"].min()
        else:
            max_1y = min_1y = None

        # Últimos 2 años
        hace_dos_anyos = hoy - timedelta(days=730)
        hist_2y = hist.loc[hace_dos_anyos:]
        if not hist_2y.empty:
            max_2y = hist_2y["High"].max()
            min_2y = hist_2y["Low"].min()
        else:
            max_2y = min_2y = None

        # ----------- ALERTAS -----------

        # Histórico
        if precio_actual >= max_historico * ALERTA_UMBRAL:
            mensaje = f"🔔 {ticker} está cerca de su MÁXIMO histórico ({precio_actual:.2f} vs {max_historico:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        if precio_actual <= min_historico * (2 - ALERTA_UMBRAL):
            mensaje = f"🔔 {ticker} está cerca de su MÍNIMO histórico ({precio_actual:.2f} vs {min_historico:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        # Último año
        if max_1y and precio_actual >= max_1y * ALERTA_UMBRAL:
            mensaje = f"📈 {ticker} está cerca de su MÁXIMO de 1 año ({precio_actual:.2f} vs {max_1y:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        if min_1y and precio_actual <= min_1y * (2 - ALERTA_UMBRAL):
            mensaje = f"📉 {ticker} está cerca de su MÍNIMO de 1 año ({precio_actual:.2f} vs {min_1y:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        # Últimos 2 años
        if max_2y and precio_actual >= max_2y * ALERTA_UMBRAL:
            mensaje = f"📈 {ticker} está cerca de su MÁXIMO de 2 años ({precio_actual:.2f} vs {max_2y:.2f})"
            alertas.append(mensaje)
            enviar_alerta(mensaje)

        if min_2y and precio_actual <= min_2y * (2 - ALERTA_UMBRAL):
            mensaje = f"📉 {ticker} está cerca de su MÍNIMO de 2 años ({precio_actual:.2f} vs {min_2y:.2f})"
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

NOMBRES_EMPRESAS = {
    "REP.MC": "Repsol - 6-7%",
    "MSFT": "Microsoft Corporation - 0.7%",
    "AAPL": "Apple Inc. - 0.5%",
    "JNJ":"Johnson & Johnson - 3.3%",
    "PG": "Procter & Gamble - 2.5%",
    "KO":"Coca-Cola - 3.1%",
    "O":"Realty Income - 5.7% mensual ",
    "CVX":"Chevron - 4.2%",
    "TTE":"TotalEnergies - 5%"

}

# Una pestaña por empresa
tabs = st.tabs([f"🏢 {ticker}" for ticker in TICKERS])
print(data)
for i, ticker in enumerate(TICKERS):
    nombre_empresa = NOMBRES_EMPRESAS.get(ticker, ticker)  # Si no está, usa el ticker
    with tabs[i]:
        st.title(nombre_empresa)

        hist = data[ticker]
        # Si el índice NO es datetime, arreglamos:
        if not isinstance(hist.index, pd.DatetimeIndex):
            hist.reset_index(inplace=True)   # Pasa la fecha a columna
            hist.set_index('Date', inplace=True) 
        print(ticker,hist)
       # Calculamos fechas de corte
        fecha_max = hist.index.max()
        fecha_corte_2y = fecha_max - pd.DateOffset(years=2)
        fecha_corte_1y = fecha_max - pd.DateOffset(years=1)

        # Filtramos datos
        hist_2y = hist[hist.index >= fecha_corte_2y]
        hist_1y = hist[hist.index >= fecha_corte_1y]

        # KPIs históricos
        precio_actual = hist["Close"].iloc[-1]
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        # KPIs 2 últimos años
        max_2y = hist_2y["High"].max()
        min_2y = hist_2y["Low"].min()

        # KPIs último año
        max_1y = hist_1y["High"].max()
        min_1y = hist_1y["Low"].min()

        # Fila 1: Histórico completo
        st.markdown("### 📜 Histórico completo")
        col1, col2, col3 = st.columns(3)
        col1.metric("📈 Máximo histórico", f"${max_historico:.2f}")
        col2.metric("📉 Mínimo histórico", f"${min_historico:.2f}")
        col3.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico histórico general
        st.markdown("### 📊 Evolución histórica del precio")
        st.line_chart(hist["Close"])

        # Fila 2: Últimos 2 años
        st.markdown("### 📅 Últimos 2 años")
        col4, col5,col6 = st.columns(3)
        col4.metric("📈 Máximo 2 años", f"${max_2y:.2f}")
        col5.metric("📉 Mínimo 2 años", f"${min_2y:.2f}")
        col6.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico ultimos 2 años
        st.markdown("### 📊 Evolución últimos 2 años del precio")
        st.line_chart(hist_2y["Close"])

        # Fila 3: Último año
        st.markdown("### 📆 Último año")
        col7, col8, col9 = st.columns(3)
        col7.metric("📈 Máximo 1 año", f"${max_1y:.2f}")
        col8.metric("📉 Mínimo 1 año", f"${min_1y:.2f}")
        col9.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico ultimo años
        st.markdown("### 📊 Evolución último año del precio")
        st.line_chart(hist_1y["Close"])


