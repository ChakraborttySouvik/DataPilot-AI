from fastapi import FastAPI

from backend.dataset import router as dataset_router
from backend.analysis import router as analysis_router
from backend.forecast import router as forecast_router
from backend.ai import router as ai_router


app = FastAPI(
    title="DataPilot AI API",
    description="Backend API for DataPilot AI",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "DataPilot AI API is running",
        "status": "healthy",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


app.include_router(dataset_router)
app.include_router(analysis_router)
app.include_router(forecast_router)
app.include_router(ai_router)