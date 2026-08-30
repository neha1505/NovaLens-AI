import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Add base directory and backend directory to path so imports work in all environments
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.routes.image_search import router as search_router
    from backend.routes.text_search import router as text_router
    from backend.routes.multimodal_search import router as multimodal_router
    from backend.routes.products import router as products_router
    from backend.routes.assistant import router as assistant_router
    from backend.routes.shopping_intelligence import router as shopping_intelligence_router
except ImportError:
    from routes.image_search import router as search_router
    from routes.text_search import router as text_router
    from routes.multimodal_search import router as multimodal_router
    from routes.products import router as products_router
    from routes.assistant import router as assistant_router
    from routes.shopping_intelligence import router as shopping_intelligence_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("NovaLens AI API startup complete. Services ready.")
    yield
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve DeepFashion images statically if present
deepfashion_dir = os.path.join(base_dir, "data", "DeepFashion")

if os.path.exists(deepfashion_dir):
    app.mount(
        "/DeepFashion",
        StaticFiles(directory=deepfashion_dir),
        name="deepfashion_images"
    )
    app.mount(
        "/images",
        StaticFiles(directory=deepfashion_dir),
        name="images_static"
    )
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
