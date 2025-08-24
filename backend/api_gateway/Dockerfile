FROM python:3.11-slim

WORKDIR /api-gateway

COPY ./api_gateway/requirements.txt /api-gateway/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /api-gateway/requirements.txt

# Install shared dependencies first to leverage Docker layer caching
COPY ./shared/requirements.txt /tmp/shared-itapia/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/shared-itapia/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN pip install -e /tmp/shared-itapia

COPY ./api_gateway /api-gateway

RUN ls -l /api-gateway