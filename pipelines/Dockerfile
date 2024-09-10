FROM python:3.10-slim

WORKDIR /pipelines-service

COPY . /pipelines-service


RUN pip install --no-cache-dir -r ./requirements/prod.txt
RUN pip install --no-cache-dir ./lib/optibet_lib-0.1-py3-none-any.whl


EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
