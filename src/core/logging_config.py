import logging
import sys

def setup_logging():
    # Formato: Hora - Nombre - Nivel de importancia - Mensaje
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/ojo_de_lisary.log") # Guardar en archivo
        ]
    )
    return logging.getLogger("OjoDeLisary")

logger = setup_logging()