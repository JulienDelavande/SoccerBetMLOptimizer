FROM ghcr.io/mlflow/mlflow:v2.15.1

<<<<<<< HEAD
WORKDIR /mlflow

COPY main.sh /mlflow

RUN pip install psycopg2-binary
RUN chmod +x main.sh

EXPOSE 80

CMD ["bash", "/mlflow/main.sh"]
=======
RUN pip install psycopg2-binary

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
>>>>>>> 4dda9b41d5f531802d381c4796d8b6ccf1a19305

