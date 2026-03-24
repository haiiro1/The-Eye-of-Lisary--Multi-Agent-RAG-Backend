import logging
import sys
import os

def setup_logging():
    # Aseguramos la carpeta para el .log y la DB de persistencia
    os.makedirs("data", exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/ojo_de_lisary.log", encoding="utf-8")
        ]
    )

    logger = logging.getLogger("OjoDeLisary")
    logger.info("👁️ El Ojo de Lisary ha despertado. Sistema de logs iniciado.")
    return logger

logger = setup_logging()