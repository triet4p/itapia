FROM python:3.11-slim

WORKDIR /data-processing

COPY ./data_processing/requirements.txt /data-processing/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /data-processing/requirements.txt

# Install shared dependencies first to leverage Docker layer caching
COPY ./shared/requirements.txt /tmp/shared-itapia/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/shared-itapia/requirements.txt

# Copy the rest of the shared code and install in editable mode (without dependencies)
COPY ./shared /tmp/shared-itapia
RUN pip install -e /tmp/shared-itapia

COPY ./data_processing /data-processing

RUN ls -l /data-processing