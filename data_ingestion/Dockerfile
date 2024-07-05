FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir /app/lib/optibet_lib-0.1-py3-none-any.whl
RUN pip install --no-cache-dir -r /app/requirements/prod.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
