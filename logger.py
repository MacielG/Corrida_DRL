import logging
import os

def setup_logger():
    """Configura o logger para o projeto Corrida DRL."""
    logger = logging.getLogger("corrida_drl")
    logger.setLevel(logging.DEBUG)
    
    # Cria diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Formato do log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler para arquivo (DEBUG, INFO, ERROR)
    file_handler = logging.FileHandler("logs/corrida_drl.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para console (apenas INFO e acima, sem DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Evita logs duplicados
    logger.propagate = False
    return logger
