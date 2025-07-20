FROM python:3.11-slim

WORKDIR /api-gateway

COPY ./api_gateway /api-gateway
COPY ./shared /tmp/shared-itapia

RUN pip install --no-cache-dir --upgrade -r /api-gateway/requirements.txt
RUN pip install -e /tmp/shared-itapia

RUN ls -l /api-gateway