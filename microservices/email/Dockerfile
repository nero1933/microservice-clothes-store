FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /email

COPY requirements.txt /email/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /email/
COPY ../../core /email/core

RUN apk add --no-cache gcc musl-dev libffi-dev

EXPOSE 8000

ENV PYTHONPATH=/email
