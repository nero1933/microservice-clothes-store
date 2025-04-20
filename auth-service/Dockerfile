FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /auth-service

COPY requirements.txt /auth-service/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /auth-service/

RUN apk add --no-cache gcc musl-dev libffi-dev

EXPOSE 8000

CMD ["python", "main.py"]

ENV PYTHONPATH=/auth-service
