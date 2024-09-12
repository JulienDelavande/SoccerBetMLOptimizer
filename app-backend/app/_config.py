"Configuration file for the app backend"

import os
from sqlalchemy import create_engine
import logging
import logging.config
import sys
from pathlib import Path
from rich.logging import RichHandler
from logger.postgressqlhandler import PostgreSQLHandler



# environment variables
ENV_VARS_REQUIRED = ["DB_TYPE", "DB_PILOT", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
                        "DB_TN_FBREF_RESULTS", "DB_TN_MODELS_RESULTS", "DB_TN_OPTIM_RESULTS",
                        "PIPELINES_PROTOCOL", "PIPELINES_HOST", "PIPELINES_PORT", 
                        "PIPELINES_ENDPOINT_INFERENCE","PIPELINES_ENDPOINT_OPTIMIZATION", "DATA_INGESTION_PROTOCOL", 
                        "DATA_INGESTION_HOST", "DATA_INGESTION_PORT", "DATA_INGESTION_ENDPOINT_FBREF", 
                        "DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS"]

DB_TYPE = os.getenv('DB_TYPE')
DB_PILOT = os.getenv('DB_PILOT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_TN_FBREF_RESULTS = os.getenv('DB_TN_FBREF_RESULTS')
DB_TN_MODELS_RESULTS = os.getenv('DB_TN_MODELS_RESULTS')
DB_TN_OPTIM_RESULTS = os.getenv('DB_TN_OPTIM_RESULTS')

PIPELINES_PROTOCOL = os.getenv('PIPELINES_PROTOCOL')
PIPELINES_HOST = os.getenv('PIPELINES_HOST')
PIPELINES_PORT = os.getenv('PIPELINES_PORT')
PIPELINES_ENDPOINT_INFERENCE = os.getenv('PIPELINES_ENDPOINT_INFERENCE')
PIPELINES_ENDPOINT_OPTIMIZATION = os.getenv('PIPELINES_ENDPOINT_OPTIMIZATION')

DATA_INGESTION_PROTOCOL = os.getenv('DATA_INGESTION_PROTOCOL')
DATA_INGESTION_HOST = os.getenv('DATA_INGESTION_HOST')
DATA_INGESTION_PORT = os.getenv('DATA_INGESTION_PORT')
DATA_INGESTION_ENDPOINT_FBREF = os.getenv('DATA_INGESTION_ENDPOINT_FBREF')
DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS = os.getenv('DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS')

for var in ENV_VARS_REQUIRED:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

# database connection
DB_URL = f'{DB_TYPE}+{DB_PILOT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
print(f'DB_URL = {DB_URL}')
engine = create_engine(DB_URL)

# logger
LOGS_DIR = Path(__file__).parent.parent / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)
LOGLEVEL = logging.DEBUG
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "minimal": {"format": "%(message)s"},
        "detailed": {
            "format": "%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d]\n%(message)s\n"  # noqa: E501
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "minimal",
            "level": logging.DEBUG,
        },
        "info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "info.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "detailed",
            "level": logging.INFO,
        },
        "error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "error.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "detailed",
            "level": logging.ERROR,
        },
        "postgresql": {
            "()": PostgreSQLHandler,
            "engine": engine,
            "service": "pipelines",
            "module": "main_module",
            "formatter": "detailed",
            "level": logging.DEBUG,
        },
        "rich": {
            "class": "rich.logging.RichHandler",
            "formatter": "minimal",
            "level": logging.DEBUG,
            "markup": True,
        },
    },
    "loggers": {
        "root": {
            "handlers": ["rich", "info", "error", "postgresql"],
            "level": LOGLEVEL,
            "propagate": True,
},
        "infer__RSF_PR_LR": {
            "handlers": [],
            "level": LOGLEVEL,
            "propagate": True,
        },
        "infer__RSF_PS_LR": {
            "handlers": [],
            "level": LOGLEVEL,
            "propagate": True,
        },
    },
}
logging.config.dictConfig(logging_config)