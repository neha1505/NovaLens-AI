from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List

try:
    from backend.schemas.product_schema import ProductSearchResult
    from backend.utils.image_utils import validate_and_load_image
    from backend.services.image_search_service import ImageSearchService
except ImportError:
    from schemas.product_schema import ProductSearchResult
    from utils.image_utils import validate_and_load_image
    from services.image_search_service import ImageSearchService

router = APIRouter()

_search_service = None

def get_search_service() -> ImageSearchService:
    global _search_service
    if _search_service is None:
        try:
            _search_service = ImageSearchService()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image Search Service is currently unavailable: {str(e)}"
            )
    return _search_service

@router.post("/image-search", response_model=List[ProductSearchResult])
async def search_by_image(
    file: UploadFile = File(...),
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Accepts an uploaded image file, processes it, and returns top K matching products.
    """
    image = await validate_and_load_image(file)

    try:
        results = search_service.search(image, top_k=10)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute visual search pipeline: {str(e)}"
        )
