FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /email

COPY /microservices/email/requirements.txt /email

RUN pip install --no-cache-dir -r requirements.txt

COPY /microservices/email /email
COPY /core /email/core

RUN apk add --no-cache gcc musl-dev libffi-dev

ENV PYTHONPATH=/email
