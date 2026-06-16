from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel, Field
from backend.schemas.product_schema import ProductSearchResult
from backend.services.text_search_service import TextSearchService

router = APIRouter()
_text_search_service = None

class TextSearchRequest(BaseModel):
    query: str = Field(..., description="The semantic search query in natural language")

def get_text_search_service() -> TextSearchService:
    global _text_search_service
    if _text_search_service is None:
        try:
            _text_search_service = TextSearchService()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Text Search Service is currently unavailable: {str(e)}"
            )
    return _text_search_service

@router.post("/text-search", response_model=List[ProductSearchResult])
async def search_by_text(
    request: TextSearchRequest,
    search_service: TextSearchService = Depends(get_text_search_service)
):
    """
    Search the product catalog for visually/semantically similar items using natural language.
    Accepts a JSON request with a 'query' string and returns the top 10 ranked products.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )

    try:
        results = search_service.search(request.query.strip(), top_k=10)
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during text search execution: {str(e)}"
        )
