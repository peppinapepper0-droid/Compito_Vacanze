FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py
COPY inizio.html /app/inizio.html
COPY info.html /app/info.html

EXPOSE 8888

CMD ["python", "server.py"]
