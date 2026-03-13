from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from api.auth import router as auth_router
from api.actions import router as actions_router
from api.sales_data import router as sales_router
from api.websocket import router as ws_router
from ml.detector import AnomalyDetector
from services.redis_service import RedisService
from services.mongodb_service import mongodb_service

# Global instances (will be initialized on startup)
detector = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up ThreatSense Backend...")
    global detector
    global redis_client
    
    # Initialize ML Model
    try:
        detector = AnomalyDetector()
        print("ML Models loaded successfully.")
    except Exception as e:
        print(f"Error loading models: {e}")
        
    # Initialize Redis
    try:
        redis_client = RedisService()
        print("Redis connection established.")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")

    # Initialize MongoDB
    await mongodb_service.connect()
        
    yield
    print("Shutting down ThreatSense Backend...")
    await mongodb_service.close()

app = FastAPI(title="ThreatSense API", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for MVP. Change in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(actions_router, prefix="/api/actions", tags=["User Actions"])
app.include_router(sales_router, prefix="/api/sales", tags=["Sales Data"])
app.include_router(ws_router, prefix="/ws", tags=["WebSockets"])

@app.get("/")
def read_root():
    return {"status": "ThreatSense MVP Backend is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
