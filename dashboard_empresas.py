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

st.set_page_config(page_title="Dashboard Empresas", layout="wide")
# Refrescar cada 1 hora (3600s)
st_autorefresh(interval=3600 * 1000, key="refresh")

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

# Función para descargar datos
@st.cache_data(ttl=3600)  # cachea 1h
def descargar_datos():
    data_historico = {}
    data_reciente = {}
    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)

            # Datos históricos (diarios)
            hist_diario = stock.history(period="max", interval="1d")
            if hist_diario.empty:
                print(f"⚠️ Histórico vacío para {ticker}")
            else:
                hist_diario = hist_diario.reset_index()
                if 'Date' not in hist_diario.columns and 'Datetime' in hist_diario.columns:
                    hist_diario.rename(columns={'Datetime': 'Date'}, inplace=True)
                elif 'Date' not in hist_diario.columns:
                    hist_diario['Date'] = hist_diario.index
                hist_diario["Date"] = pd.to_datetime(hist_diario["Date"])
                data_historico[ticker] = hist_diario

            # Datos recientes (1 hora)
            hist_reciente = stock.history(period="2y", interval="1h")
            if hist_reciente.empty:
                print(f"⚠️ Recientes vacíos para {ticker}")
            else:
                hist_reciente = hist_reciente.reset_index()
                if 'Date' not in hist_reciente.columns and 'Datetime' in hist_reciente.columns:
                    hist_reciente.rename(columns={'Datetime': 'Date'}, inplace=True)
                elif 'Date' not in hist_reciente.columns:
                    hist_reciente['Date'] = hist_reciente.index
                hist_reciente["Date"] = pd.to_datetime(hist_reciente["Date"])
                data_reciente[ticker] = hist_reciente

        except Exception as e:
            print(f"❌ Error descargando {ticker}: {e}")
            continue

    return data_historico, data_reciente

# Función para enviar alerta por correo
def enviar_alerta(mensaje):
    try:
        mensaje = str(mensaje)  # Asegura que es string

        # Muy importante: charset utf-8 para soportar emojis
        msg = MIMEText(mensaje, _charset="utf-8")
        msg["Subject"] = "🔔 Alerta de Mercado"
        msg["From"] = EMAIL_ALERTA
        msg["To"] = EMAIL_ALERTA

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ALERTA, EMAIL_CONTRASENA)
            server.send_message(msg)
        print(f"✅ Correo enviado correctamente: {mensaje}")
    except Exception as e:
        print(f"Error al enviar correo: {e}")


def check_alertas(datos_historicos, datos_recientes):
    alertas = []
    hoy = datetime.now()

    for ticker in datos_historicos.keys():
        hist = datos_historicos[ticker]
        reciente = datos_recientes[ticker]

        # Aseguramos que 'Date' sea índice
        if 'Date' in hist.columns:
            hist.set_index('Date', inplace=True)
        if 'Date' in reciente.columns:
            reciente.set_index('Date', inplace=True)

        hist.index = pd.to_datetime(hist.index).tz_localize(None)      # <<< AÑADIDO
        reciente.index = pd.to_datetime(reciente.index).tz_localize(None)  # <<< AÑADIDO


        precio_actual = reciente["Close"].iloc[-1]

        # Histórico completo (diario)
        max_historico = hist["High"].max()
        min_historico = hist["Low"].min()

        # Últimos 2 años (datos 1h)
        fecha_corte_2y = hoy - timedelta(days=730)
        reciente_2y = reciente.loc[reciente.index >= fecha_corte_2y]
        if not reciente_2y.empty:
            max_2y = reciente_2y["High"].max()
            min_2y = reciente_2y["Low"].min()
        else:
            max_2y = min_2y = None

        # Último año (datos 1h)
        fecha_corte_1y = hoy - timedelta(days=365)
        reciente_1y = reciente.loc[reciente.index >= fecha_corte_1y]
        if not reciente_1y.empty:
            max_1y = reciente_1y["High"].max()
            min_1y = reciente_1y["Low"].min()
        else:
            max_1y = min_1y = None

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

data_historico, data_reciente = descargar_datos()

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

alertas = check_alertas(data_historico,data_reciente)

