FROM continuumio/miniconda3

# Set working directory
WORKDIR /ai-service-quick

# --- STEP 1: CREATE NEW CONDA ENVIRONMENT WITH SPECIFIC PYTHON VERSION ---
# This is the best practice to control version.
# We create an environment named 'itapia' with Python 3.11
RUN conda create -n itapia python=3.11 -y

# --- STEP 2: ACTIVATE NEW ENVIRONMENT AND INSTALL LIBRARIES ---
# Use 'conda run' to execute commands inside the 'itapia' environment
# 2.1. Install TA-Lib first
RUN conda run -n itapia conda install -c conda-forge -y ta-lib "spacy=3.6.*" pandas-ta

# 2.2. Install remaining packages with pip
COPY ./ai_service_quick/requirements.txt /ai-service-quick/requirements.txt
RUN conda run -n itapia pip install --no-cache-dir --upgrade -r /ai-service-quick/requirements.txt

# --- STEP 3: COPY LOCAL MODEL ---
# Copy pre-downloaded wheel model
COPY ./ai_service_quick/dependencies/en_core_web_md-3.6.0-py3-none-any.whl /tmp/
# Install model from local wheel, ensuring reproducible
RUN conda run -n itapia pip install /tmp/en_core_web_md-3.6.0-py3-none-any.whl

# Install shared dependencies first to leverage Docker layer caching
COPY ./shared/requirements.txt /tmp/shared-itapia/requirements.txt
RUN conda run -n itapia pip install --no-cache-dir --upgrade -r /tmp/shared-itapia/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN conda run -n itapia pip install -e /tmp/shared-itapia

COPY ./ai_service_quick /ai-service-quick

RUN chmod +x /ai-service-quick/entrypoint.sh

RUN ls /ai-service-quick -l