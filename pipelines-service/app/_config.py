"Configuration file for the pipelines service"

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from logs.postgressqlhandler import PostgreSQLHandler

# environment variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_TN_FBREF_RESULTS = os.getenv('DB_TN_FBREF_RESULTS')
DB_TN_SOFIFA_TEAMS_STATS = os.getenv('DB_TN_SOFIFA_TEAMS_STATS')
DB_TN_MODELS_RESULTS = os.getenv('DB_TN_MODELS_RESULTS')
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI')

# database connection
db_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)

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
