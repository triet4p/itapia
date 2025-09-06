from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["Root"])
def read_root():
    """Root endpoint that returns a welcome message.
    
    Returns:
        dict: Welcome message for the API
    """
    return {"message": "Welcome to ITAPIA AI Quick Service"}