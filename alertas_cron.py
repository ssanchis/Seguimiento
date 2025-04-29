# alertas_cron.py

from alertas_core import descargar_datos, check_alertas
import time
import datetime

def main():
    while True:
        print(f"🚀 Ejecutando script de alertas... {datetime.datetime.now()}")
        datos_hist, datos_recientes = descargar_datos()
        alertas = check_alertas(datos_hist, datos_recientes)
        if alertas:
            print('Find', len(alertas),'alertas')
        print("✅ Esperando 1 hora para la siguiente ejecución...\n")
        time.sleep(3600)  # 3600 segundos = 1 hora

if __name__ == "__main__":
    main()
