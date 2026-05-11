FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

VOLUME ["/app/data"]

EXPOSE 5003

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
