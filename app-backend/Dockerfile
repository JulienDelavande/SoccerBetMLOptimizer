FROM python:3.10-slim

WORKDIR /app-backend

COPY . /app-backend

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ./lib/optibet_lib-0.1-py3-none-any.whl

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]