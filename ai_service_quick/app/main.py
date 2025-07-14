from fastapi import FastAPI
from app.api.v1.endpoints import quick_analysis
from app.core.config import AI_QUICK_V1_BASE_ROUTE

app = FastAPI(
    title="ITAPIA AI Service Quick",
    description="API nội bộ cho quy trình phân tích nhanh của AI Service",
    version="1.0.0"
)

# Bao gồm router từ file data_viewer
app.include_router(quick_analysis.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA AI Quick Service"}