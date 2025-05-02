# alertas_cron.py

from alertas_core import descargar_datos, check_alertas
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')


def main():
    print(f"🚀 Ejecutando script de alertas... {datetime.datetime.now()}")
    datos_hist, datos_recientes = descargar_datos()
    alertas = check_alertas(datos_hist, datos_recientes)
    if alertas:
        print('Find', len(alertas),'alertas')
    else:
        print("✅ No se encontraron alertas.")
    
if __name__ == "__main__":
    main()
