from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import pickle
import os

from app.routes import auth, farmer, agronomist, researcher, ml_models
from app.models.database import init_db

# Global variable to store ML models
ml_models_cache = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML models on startup
    try:
        # Load yield prediction model
        if os.path.exists("app/ml_models/yield_model.pkl"):
            with open("app/ml_models/yield_model.pkl", "rb") as f:
                ml_models_cache["yield_model"] = pickle.load(f)
        
        # Load crop health model
        if os.path.exists("app/ml_models/crop_health_model.pkl"):
            with open("app/ml_models/crop_health_model.pkl", "rb") as f:
                ml_models_cache["crop_health_model"] = pickle.load(f)
        
        print("ML models loaded successfully")
    except Exception as e:
        print(f"Error loading ML models: {e}")
    
    # Initialize database
    await init_db()
    
    yield
    
    # Cleanup on shutdown
    ml_models_cache.clear()

app = FastAPI(
    title="Agriculture Insights API",
    description="A comprehensive platform for agricultural data analysis and predictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(farmer.router, prefix="/api/farmer", tags=["farmer"])
app.include_router(agronomist.router, prefix="/api/agronomist", tags=["agronomist"])
app.include_router(researcher.router, prefix="/api/researcher", tags=["researcher"])
app.include_router(ml_models.router, prefix="/api/ml", tags=["machine-learning"])

@app.get("/")
async def root(request: Request):
    """Serve the landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "models_loaded": len(ml_models_cache)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)