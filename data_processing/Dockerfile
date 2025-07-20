FROM python:3.11-slim

WORKDIR /data-processing

COPY ./data_processing /data-processing
COPY ./shared /tmp/shared-itapia

RUN pip install --no-cache-dir --upgrade -r /data-processing/requirements.txt
RUN pip install -e /tmp/shared-itapia

RUN ls -l /data-processing