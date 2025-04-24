FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /users

COPY requirements.txt /users/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /users/
COPY ../../core /users/core

RUN apk add --no-cache gcc musl-dev libffi-dev

EXPOSE 8000

ENV PYTHONPATH=/users:/users/core
