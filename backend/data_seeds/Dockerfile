FROM python:3.11-slim

WORKDIR /data-seeds

#COPY ./data_seeds/requirements.txt /data-seeds/requirements.txt
#RUN pip install --no-cache-dir --upgrade -r /data-seeds/requirements.txt

# Install shared dependencies first to leverage Docker layer caching
COPY ./shared/requirements.txt /tmp/shared-itapia/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/shared-itapia/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN pip install -e /tmp/shared-itapia

COPY ./data_seeds /data-seeds

RUN ls -l /data-seeds