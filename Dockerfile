# Simple Flask Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Use a writable instance folder
RUN mkdir -p /app/instance && chmod -R 777 /app/instance

EXPOSE 8080
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
