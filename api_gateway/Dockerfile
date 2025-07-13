FROM python:3.13-slim

WORKDIR /api-service

COPY ./requirements.txt /api-service/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /api-service/requirements.txt

COPY . /api-service

RUN ls /api-service -l
