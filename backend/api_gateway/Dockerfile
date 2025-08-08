FROM python:3.11-slim

WORKDIR /api-gateway

COPY ./api_gateway/requirements.txt /api-gateway/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /api-gateway/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN pip install -e /tmp/shared-itapia

COPY ./api_gateway /api-gateway

RUN ls -l /api-gateway