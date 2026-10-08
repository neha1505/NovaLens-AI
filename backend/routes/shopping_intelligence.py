from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
try:
    from backend.services.image_search_service import ImageSearchService
    from backend.routes.image_search import get_search_service
    from backend.services.shopping_intelligence_service import ShoppingIntelligenceService
except ImportError:
    from services.image_search_service import ImageSearchService
    from routes.image_search import get_search_service
    from services.shopping_intelligence_service import ShoppingIntelligenceService

router = APIRouter()

class RetailerOfferResponse(BaseModel):
    product_name: str
    product_image: str
    image_url: str
    price: float
    rating: float
    review_count: int
    brand: str
    retailer: str
    shopping_score: float
    is_best_price: bool
    is_best_quality: bool
    is_best_value: bool
    is_most_popular: bool

class ShoppingAnalysisResponse(BaseModel):
    best_price_explanation: str
    best_quality_explanation: str
    best_overall_explanation: str
    buying_summary: str

class CompareOffersResponse(BaseModel):
    results: List[RetailerOfferResponse]
    ai_analysis: ShoppingAnalysisResponse

@router.get("/products/{product_id}/compare", response_model=CompareOffersResponse)
async def compare_product_offers(
    product_id: str,
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Retrieves and compares offers across trusted retailers for a given catalog product_id.
    Uses multi-factor scoring and invokes the AI Buying Recommendation.
    """
    if search_service.metadata is None:
        search_service.load_index_and_metadata()

    # Retrieve target product details from loaded metadata list
    target_product = None
    for p in search_service.metadata:
        if p.get("product_id") == product_id:
            target_product = p
            break

    if not target_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found in catalog."
        )

    shopping_service = ShoppingIntelligenceService()
    try:
        # 1. Retrieve retailer offers asynchronously
        raw_offers = await shopping_service.retrieve_retailer_offers(target_product)
        
        # 2. Score and highlight best options
        scored_offers = shopping_service.score_offers(raw_offers)
        
        # 3. Call LLM for buying analysis
        ai_recommendations = await shopping_service.generate_shopping_analysis(target_product, scored_offers)
        
        return CompareOffersResponse(
            results=[RetailerOfferResponse(**o) for o in scored_offers],
            ai_analysis=ShoppingAnalysisResponse(**ai_recommendations)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate shopping intelligence comparison: {str(e)}"
        )

