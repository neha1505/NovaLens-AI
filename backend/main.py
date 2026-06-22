import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Add base directory to path so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.routes.image_search import router as search_router, get_search_service
from backend.routes.text_search import router as text_router
from backend.routes.multimodal_search import router as multimodal_router
from backend.routes.products import router as products_router
from backend.routes.assistant import router as assistant_router
from backend.routes.shopping_intelligence import router as shopping_intelligence_router
from ml.clip.clip_loader import CLIPLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-warm models and services
    print("Pre-warming CLIP model and loading FAISS index...")
    try:
        # Load CLIP singleton
        clip_loader = CLIPLoader()
        clip_loader.get_model_and_preprocess()
        
        # Load FAISS index in search service
        search_service = get_search_service()
        if search_service.index is None:
            print("Warning: FAISS index is empty or not built yet.")
    except Exception as e:
        print(f"Error during startup pre-warming: {e}")
    
    yield
    # Shutdown
    print("Shutting down NovaLens AI Backend.")

app = FastAPI(
    title="NovaLens AI API",
    description="Multimodal fashion discovery backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict to frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve DeepFashion images statically
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
deepfashion_dir = os.path.join(base_dir, "data", "DeepFashion")

if os.path.exists(deepfashion_dir):
    app.mount("/images/DeepFashion", StaticFiles(directory=deepfashion_dir), name="deepfashion_images")
    print(f"Mounted static DeepFashion images folder from: {deepfashion_dir}")
else:
    print(f"Warning: DeepFashion folder does not exist at {deepfashion_dir}")

# Include search routes
app.include_router(search_router, prefix="/api")
app.include_router(text_router, prefix="/api")
app.include_router(multimodal_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(shopping_intelligence_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to NovaLens AI API. Multimodal search backend is online."}
