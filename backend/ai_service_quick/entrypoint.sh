#!/bin/bash

# Important!!! This command will find `conda.sh` and
# "source" to any command like 'active itapia' is executable
source /opt/conda/etc/profile.d/conda.sh

conda activate itapia

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload