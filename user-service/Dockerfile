FROM python:3.13-alpine
LABEL authors="nero"

WORKDIR /user-service

COPY requirements.txt /user-service/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /user-service/

RUN apk add --no-cache gcc musl-dev libffi-dev

EXPOSE 8000

CMD ["python", "main.py"]

ENV PYTHONPATH=/user-service
