from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import List

try:
    from backend.schemas.product_schema import ProductSearchResult
    from backend.utils.image_utils import validate_and_load_image
    from backend.services.multimodal_search_service import MultimodalSearchService
except ImportError:
    from schemas.product_schema import ProductSearchResult
    from utils.image_utils import validate_and_load_image
    from services.multimodal_search_service import MultimodalSearchService

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

@router.post("/multimodal-search")
async def search_multimodal(
    file: UploadFile = File(None),
    image: UploadFile = File(None),
    text_prompt: str = Form(""),
    query_text: str = Form(""),
    weight: float = Form(None),
    image_weight: float = Form(None),
    multimodal_service: MultimodalSearchService = Depends(get_multimodal_service)
):
    """
    Combines an uploaded image with an optional text prompt and a blend weight parameter [0.0 - 1.0].
    Returns top matching products along with real-time explainability vector fusion details.
    """
    upload_file = file or image
    prompt = text_prompt or query_text
    blend_weight = weight if weight is not None else (image_weight if image_weight is not None else 0.5)

    if not upload_file and not prompt:
        raise HTTPException(
            status_code=400,
            detail="Please provide an image file or a text query for multimodal search."
        )

    loaded_image = None
    if upload_file and upload_file.filename:
        loaded_image = await validate_and_load_image(upload_file)

    if blend_weight < 0.0 or blend_weight > 1.0:
        raise HTTPException(
            status_code=400,
            detail="Blend weight must be a float value between 0.0 and 1.0."
        )

    try:
        results = multimodal_service.search(
            image=loaded_image,
            query_text=prompt,
            image_weight=blend_weight,
            top_k=10
        )
        
        # Map raw dictionary objects to validated ProductSearchResult schemas
        formatted_results = [ProductSearchResult(**r) for r in results]
        
        return {
            "results": formatted_results,
            "explainability": {
                "text_prompt": prompt,
                "image_weight": blend_weight,
                "text_weight": 1.0 - blend_weight
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute multimodal search pipeline: {str(e)}"
        )
