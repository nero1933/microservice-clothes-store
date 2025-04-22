FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /users-service

COPY requirements.txt /users-service/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /users-service/

RUN apk add --no-cache gcc musl-dev libffi-dev

EXPOSE 8000

ENV PYTHONPATH=/users-service
