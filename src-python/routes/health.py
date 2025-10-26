from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])

# This will be set by main.py
POINTER_BACKEND_AVAILABLE = False


@router.get("/")
async def root():
    return {
        "name": "Pointer Backend",
        "version": "1.0.0",
        "status": "running",
        "pointer_backend_available": POINTER_BACKEND_AVAILABLE
    }


@router.get("/health")
async def health():
    return {"status": "healthy", "pointer_backend_available": POINTER_BACKEND_AVAILABLE}
