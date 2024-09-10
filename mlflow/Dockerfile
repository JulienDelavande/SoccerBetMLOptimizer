FROM ghcr.io/mlflow/mlflow:v2.15.1

RUN pip install psycopg2-binary

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]

