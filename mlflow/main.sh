#!/bin/bash

mlflow server --host 0.0.0.0 \
              --port 80 \
              --backend-store-uri ${DB_TYPE}+${DB_PILOT}://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}