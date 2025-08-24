FROM python:3.11-slim

WORKDIR /evo-worker

COPY ./evo_worker/requirements.txt /evo-worker/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /evo-worker/requirements.txt

# Install shared dependencies first to leverage Docker layer caching
COPY ./shared/requirements.txt /tmp/shared-itapia/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/shared-itapia/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN pip install -e /tmp/shared-itapia

COPY ./evo_worker /evo-worker

RUN ls -l /evo-worker