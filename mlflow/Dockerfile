FROM ghcr.io/mlflow/mlflow:v2.15.1

WORKDIR /mlflow

COPY . /mlflow

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x main.sh

EXPOSE 80

CMD ["bash", "/mlflow/main.sh"]

