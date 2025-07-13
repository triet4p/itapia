FROM python:3.13-slim

WORKDIR /api-gateway

COPY ./requirements.txt /api-gateway/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /api-gateway/requirements.txt

COPY . /api-gateway

RUN ls /api-gateway -l
