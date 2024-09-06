#!/bin/sh

mlflow server --host 0.0.0.0 \
              --port ${MLFLOW_WEBSERVER_CONTAINER_PORT} \
              --backend-store-uri postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}