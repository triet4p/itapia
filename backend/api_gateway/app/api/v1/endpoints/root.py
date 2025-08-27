from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: A welcome message for the ITAPIA API Service
    """
    return {"message": "Welcome to ITAPIA API Service"}