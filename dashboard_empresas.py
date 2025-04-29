# dashboard_empresas.py

import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
import schedule
import time
import threading
from datetime import datetime, timedelta
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
from alertas_core import descargar_datos

st.set_page_config(page_title="Dashboard Empresas", layout="wide")
# Refrescar cada 1 hora (3600s)
count = st_autorefresh(interval=3600*1000, key="refresh") 

if count > 0:
    st.cache_data.clear()  

zona_madrid = ZoneInfo("Europe/Madrid")

# Hora actual en Madrid
hora_actual = datetime.now(tz=zona_madrid)
proxima_actualizacion = hora_actual + timedelta(hours=1)

# Mostrar formateado
st.sidebar.markdown(f"🕑 **Última actualización:** {hora_actual.strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.markdown(f"🔜 **Próxima actualización:** {proxima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")

# ------------------------------------------
# CONFIGURACIÓN
PASSWORD = "soyrica"  # Cambia aquí tu contraseña
TICKERS = ["AAPL", "MSFT","JNJ","REP.MC", "PG", "KO","O","CVX","TTE"]  # Empresas que quieres seguir
ALERTA_UMBRAL = 0.98  # 98% del máximo o 102% del mínimo
EMAIL_ALERTA = "ssanchiscasco@gmail.com"  # Cambia aquí tu correo para recibir alertas
EMAIL_CONTRASENA = "icxn wgnh dmfx ztim"  # Tu contraseña de correo
# ------------------------------------------

# Dashboard principal
st.title("📊 Seguimiento de Empresas")

data_historico, data_reciente = descargar_datos()

NOMBRES_EMPRESAS = {
    "REP.MC": "Repsol - 6~7%",
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

for i, ticker in enumerate(TICKERS):
    nombre_empresa = NOMBRES_EMPRESAS.get(ticker, ticker)  # Si no está, usa el ticker
    with tabs[i]:
        st.title(nombre_empresa)

        hist = data_historico[ticker]
        reciente = data_reciente[ticker]

        # Aseguramos índices
        if not isinstance(hist.index, pd.DatetimeIndex):
            hist.reset_index(inplace=True)
            hist.set_index('Date', inplace=True)

        if not isinstance(reciente.index, pd.DatetimeIndex):
            reciente.reset_index(inplace=True)
            reciente.set_index('Date', inplace=True)

        # Calculamos fechas de corte
        fecha_max = reciente.index.max()
        fecha_corte_2y = fecha_max - pd.DateOffset(years=2)
        fecha_corte_1y = fecha_max - pd.DateOffset(years=1)

        # Filtramos datos recientes
        reciente_2y = reciente[reciente.index >= fecha_corte_2y]
        reciente_1y = reciente[reciente.index >= fecha_corte_1y]

        # KPIs históricos
        precio_actual = reciente["Close"].iloc[-1]  # precio actual en reciente
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        # KPIs 2 últimos años (usando datos horarios)
        max_2y = reciente_2y["High"].max()
        min_2y = reciente_2y["Low"].min()

        # KPIs último año
        max_1y = reciente_1y["High"].max()
        min_1y = reciente_1y["Low"].min()

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
        col4, col5, col6 = st.columns(3)
        col4.metric("📈 Máximo 2 años", f"${max_2y:.2f}")
        col5.metric("📉 Mínimo 2 años", f"${min_2y:.2f}")
        col6.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico últimos 2 años
        st.markdown("### 📊 Evolución últimos 2 años del precio (1h)")
        st.line_chart(reciente_2y["Close"])

        # Fila 3: Último año
        st.markdown("### 📆 Último año")
        col7, col8, col9 = st.columns(3)
        col7.metric("📈 Máximo 1 año", f"${max_1y:.2f}")
        col8.metric("📉 Mínimo 1 año", f"${min_1y:.2f}")
        col9.metric("💵 Precio actual", f"${precio_actual:.2f}")

        # Gráfico último año
        st.markdown("### 📊 Evolución último año del precio (1h)")
        st.line_chart(reciente_1y["Close"])
        print(reciente_1y)

