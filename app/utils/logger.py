import logging
import sys
def get_logger(name: str = "ocr-llm-mvp") -> logging.Logger:
   logger = logging.getLogger(name)
   if logger.handlers:
      return logger
   logger.setLevel(logging.INFO)
   handler = logging.StreamHandler(sys.stdout)
   formatter = logging.Formatter("[%(levelname)s] %(message)s")
   handler.setFormatter(formatter)
   logger.addHandler(handler)
   logger.propagate = False
   return logger
