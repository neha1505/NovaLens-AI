from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
try:
    from backend.services.image_search_service import ImageSearchService
    from backend.routes.image_search import get_search_service
    from backend.utils.search_helpers import execute_faiss_search, retrieve_product_metadata
    from backend.services.outfit_service import OutfitService
except ImportError:
    from services.image_search_service import ImageSearchService
    from routes.image_search import get_search_service
    from utils.search_helpers import execute_faiss_search, retrieve_product_metadata
    from services.outfit_service import OutfitService

router = APIRouter()

class ProductDetailResponse(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    price: float
    image_path: str

class ProductSimilarResponse(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_path: str
    similarity_score: float

@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str,
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Retrieve product details for a given product_id using the loaded metadata.
    """
    if search_service.metadata is None:
        search_service.load_index_and_metadata()

    # Look up product details in loaded metadata list
    product = None
    for p in search_service.metadata:
        if p.get("product_id") == product_id:
            product = p
            break

    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found."
        )

    return ProductDetailResponse(
        product_id=product["product_id"],
        name=product["name"],
        category=product["category"],
        description=product["description"],
        price=product["price"],
        image_path=product["image_path"]
    )

@router.get("/products/{product_id}/similar", response_model=List[ProductSimilarResponse])
async def get_similar_products(
    product_id: str,
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Retrieve the top 8 similar products for a given product_id.
    Uses FAISS index reconstruction to query visual embeddings.
    """
    if search_service.index is None or search_service.metadata is None:
        search_service.load_index_and_metadata()

    # 1. Locate index position of the product in the metadata
    product_idx = -1
    for i, p in enumerate(search_service.metadata):
        if p.get("product_id") == product_id:
            product_idx = i
            break

    if product_idx == -1:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found in catalog."
        )

    # 2. Reconstruct the vector embedding from FAISS using the index position
    try:
        query_vector = search_service.index.reconstruct(product_idx)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve vector embedding for product ID {product_id}: {str(e)}"
        )

    # 3. Query the FAISS index for closest matches
    # Search for top_k = 10 to allow filtering out the product itself
    top_k = 10
    try:
        distances, indices = execute_faiss_search(search_service.index, query_vector, top_k)
        results = retrieve_product_metadata(search_service.metadata, indices, distances)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying index database: {str(e)}"
        )

    # 4. Filter out the selected product and return the top 8 matches
    similar_products = []
    for res in results:
        if res.get("product_id") == product_id:
            continue
            
        similar_products.append(ProductSimilarResponse(
            product_id=res["product_id"],
            name=res["name"],
            category=res["category"],
            price=res["price"],
            image_path=res["image_path"],
            similarity_score=res.get("similarity_score", 0.0)
        ))
        
        if len(similar_products) == 8:
            break

    return similar_products

class RecommendationResponse(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_path: str
    similarity_score: float

@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_personalized_recommendations(
    product_ids: str = Query("", description="Comma-separated list of recently viewed product IDs"),
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Retrieve personalized fashion recommendations based on recently viewed product IDs.
    Queries FAISS for each viewed item, merges results, filters viewed items, and returns top 8.
    """
    if not product_ids or not product_ids.strip():
        return []

    viewed_ids = [pid.strip() for pid in product_ids.split(",") if pid.strip()]
    if not viewed_ids:
        return []

    if search_service.index is None or search_service.metadata is None:
        search_service.load_index_and_metadata()

    # Exclude viewed products from recommendation candidates
    viewed_set = set(viewed_ids)

    # Dictionary to keep best score for each candidate product ID
    candidates = {}

    for pid in viewed_ids:
        # 1. Locate index position
        product_idx = -1
        for i, p in enumerate(search_service.metadata):
            if p.get("product_id") == pid:
                product_idx = i
                break

        if product_idx == -1:
            continue  # Gracefully skip if product not found

        # 2. Reconstruct query vector
        try:
            query_vector = search_service.index.reconstruct(product_idx)
        except Exception:
            continue  # Gracefully skip reconstruction errors

        # 3. Query FAISS index for top 12 matches (leaving room for exclusion of viewed items)
        try:
            distances, indices = execute_faiss_search(search_service.index, query_vector, top_k=12)
            results = retrieve_product_metadata(search_service.metadata, indices, distances)
        except Exception:
            continue

        # 4. Merge candidates
        for res in results:
            candidate_id = res.get("product_id")
            # Do not recommend items that are in the recently viewed history
            if candidate_id in viewed_set:
                continue

            similarity = res.get("similarity_score", 0.0)
            if candidate_id not in candidates or similarity > candidates[candidate_id]["similarity_score"]:
                candidates[candidate_id] = {
                    "product_id": candidate_id,
                    "name": res.get("name", ""),
                    "category": res.get("category", ""),
                    "price": res.get("price", 0.0),
                    "image_path": res.get("image_path", ""),
                    "similarity_score": similarity
                }

    # 5. Rank by similarity descending
    ranked_candidates = list(candidates.values())
    ranked_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

    # 6. Return top 8 recommendations
    return [RecommendationResponse(**item) for item in ranked_candidates[:8]]

class OutfitProductResponse(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_path: str

class OutfitRecommendationResponse(BaseModel):
    outfit_name: str
    style: str
    explanation: str
    products: List[OutfitProductResponse]

@router.get("/products/{product_id}/outfit", response_model=OutfitRecommendationResponse)
async def get_outfit_recommendation(
    product_id: str,
    recently_viewed: Optional[str] = Query("", description="Comma-separated recently viewed product IDs"),
    search_service: ImageSearchService = Depends(get_search_service)
):
    """
    Retrieve outfit recommendation for a given product_id.
    """
    viewed_ids = []
    if recently_viewed and recently_viewed.strip():
        viewed_ids = [pid.strip() for pid in recently_viewed.split(",") if pid.strip()]
        
    outfit_service = OutfitService(search_service)
    try:
        res = await outfit_service.generate_outfit(product_id, viewed_ids)
        return OutfitRecommendationResponse(
            outfit_name=res["outfit_name"],
            style=res["style"],
            explanation=res["explanation"],
            products=[OutfitProductResponse(**item) for item in res["products"]]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outfit recommendation: {str(e)}")
