# alertas_cron.py

from alertas_core import descargar_datos, check_alertas

def main():
    print("🚀 Ejecutando script de alertas...")
    datos_hist, datos_recientes = descargar_datos()
    check_alertas(datos_hist, datos_recientes)

if __name__ == "__main__":
    main()
