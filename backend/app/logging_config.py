import logging
import json
import os

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        # Inclut directement les attributs métier à la racine du JSON
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_record.update(record.extra_data)
            
        return json.dumps(log_record)

def setup_logging():
    # S'assurer que le dossier logs existe
    os.makedirs("logs", exist_ok=True)
    
    # Formateur JSON
    formatter = JsonFormatter()
    
    # Handler 1 : Écriture dans le fichier logs/app.log (lu par Filebeat)
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    
    # Handler 2 : Console Terminal
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    # Configuration du logger principal
    root_logger = logging.getLogger("fastapi_app")
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [file_handler, stream_handler]