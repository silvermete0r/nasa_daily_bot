FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

COPY . .

CMD ["python", "main.py"]