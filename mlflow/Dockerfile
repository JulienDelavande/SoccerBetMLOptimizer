FROM ghcr.io/mlflow/mlflow:v2.15.1

WORKDIR /mlflow

COPY main.sh /mlflow

RUN pip install psycopg2-binary
RUN chmod +x main.sh

EXPOSE 80

CMD ["bash", "/mlflow/main.sh"]

