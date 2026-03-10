import logging
import sys
import os

def setup_logging():
    # Aseguramos que la carpeta data exista para evitar errores al crear el .log
    os.makedirs("data", exist_ok=True) # evitas que la aplicación falle si intentas iniciar el logger en un contenedor o servidor

    # Formato: Hora - Nombre - Nivel de importancia - Mensaje
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/ojo_de_lisary.log", encoding="utf-8") #encoding para caracteres D&D
        ]
    )

    logger = logging.getLogger("OjoDeLisary")
    logger.info("👁️ El Ojo de Lisary ha despertado. Sistema de logs iniciado.")
    return logger

logger = setup_logging()