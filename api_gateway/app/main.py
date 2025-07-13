from fastapi import FastAPI

import os
init_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(init_dir)
import sys
sys.path.append(init_dir)

from app.api.v1.endpoints import data_viewer
from app.core.config import API_V1_BASE_ROUTE

app = FastAPI(
    title="ITAPIA API Service",
    description="API Gateway cho hệ thống ITAPIA, phục vụ dữ liệu và điều phối các tác vụ AI.",
    version="1.0.0"
)

# Bao gồm router từ file data_viewer
app.include_router(data_viewer.router, prefix=API_V1_BASE_ROUTE, tags=["Data Viewer"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA API Service"}