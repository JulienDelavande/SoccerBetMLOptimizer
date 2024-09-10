FROM python:3.10-slim

WORKDIR /app-frontend

COPY . /app-frontend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["streamlit", "run", "main.py", "--server.port", "80"]

