from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import List
from backend.schemas.product_schema import ProductSearchResult
from backend.utils.image_utils import validate_and_load_image
from backend.services.multimodal_search_service import MultimodalSearchService

router = APIRouter()
_multimodal_search_service = None

def get_multimodal_service() -> MultimodalSearchService:
    global _multimodal_search_service
    if _multimodal_search_service is None:
        try:
            _multimodal_search_service = MultimodalSearchService()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Multimodal Search Service is currently unavailable: {str(e)}"
            )
    return _multimodal_search_service

@router.post("/multimodal-search", response_model=List[ProductSearchResult])
async def search_multimodal(
    image: UploadFile = File(None),
    query_text: str = Form(None),
    image_weight: float = Form(0.7),
    search_service: MultimodalSearchService = Depends(get_multimodal_service)
):
    """
    Search the product catalog combining visual (image) and textual intent using embedding fusion.
    Requires an uploaded image file, query text, and an optional image_weight form parameter.
    """
    # 1. Validation for empty requests or missing elements
    clean_query = query_text.strip() if query_text is not None else None
    
    if image is None and (clean_query is None or clean_query == ""):
        raise HTTPException(
            status_code=400,
            detail="Request is empty. Please upload an image, enter query text, or both."
        )

    if not (0.0 <= image_weight <= 1.0):
        raise HTTPException(
            status_code=400,
            detail="Image weight influence must be between 0.0 and 1.0."
        )

    # 2. Validate and convert image upload to PIL Image if present
    pil_image = None
    if image is not None:
        try:
            pil_image = validate_and_load_image(image)
        except HTTPException as e:
            # Re-raise explicit HTTP exceptions from image validation utility
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted image format: {str(e)}"
            )

    # 3. Execute fused search query
    try:
        results = search_service.search(pil_image, clean_query, image_weight, top_k=10)
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during multimodal search execution: {str(e)}"
        )
