import os
import sys
import re
from typing import List, Dict, Any

# Ensure base directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.image_search_service import ImageSearchService
from ml.clip.text_embedding import get_text_embedding
from backend.utils.search_helpers import (
    execute_faiss_search,
    retrieve_product_metadata,
    calibrate_similarity_score,
    SearchPerformanceTimer
)

STOP_WORDS = {"a", "an", "the", "in", "on", "at", "for", "with", "and", "or", "of", "to", "is", "are"}

CATEGORY_SYNONYMS = {
    "dress": ["dresses", "dress"],
    "dresses": ["dresses", "dress"],
    "shirt": ["blouses_shirts", "shirts_polos", "shirt"],
    "shirts": ["blouses_shirts", "shirts_polos", "shirt"],
    "jacket": ["jackets_vests", "jackets_coats", "jacket"],
    "jackets": ["jackets_vests", "jackets_coats", "jacket"],
    "coat": ["jackets_coats", "coat"],
    "coats": ["jackets_coats", "coat"],
    "jeans": ["denim", "pants", "jeans"],
    "shorts": ["shorts"],
    "skirt": ["skirts", "skirt"],
    "skirts": ["skirts", "skirt"],
    "blouse": ["blouses_shirts", "blouse"],
    "hoodie": ["sweatshirts_hoodies", "hoodie"],
    "sweater": ["sweaters", "cardigans", "sweater"],
    "jumpsuit": ["rompers_jumpsuits", "jumpsuit"],
    "romper": ["rompers_jumpsuits", "romper"]
}

def compute_keyword_score(query_tokens: List[str], product: Dict[str, Any]) -> float:
    if not query_tokens:
        return 0.0
    
    name = product.get("name", "").lower()
    category = product.get("category", "").lower()
    desc = product.get("description", "").lower()
    prod_id = product.get("product_id", "").lower()
    
    matches = 0.0
    
    for token in query_tokens:
        synonyms = CATEGORY_SYNONYMS.get(token, [token])
        if any(syn in category for syn in synonyms) or any(syn in name for syn in synonyms):
            matches += 1.5
        elif token in name:
            matches += 1.0
        elif token in desc:
            matches += 0.5
            
    # Gender matching adjustment
    is_women_query = any(w in query_tokens for w in ["women", "womens", "woman", "female", "ladies", "girl", "girls"])
    is_men_query = any(m in query_tokens for m in ["men", "mens", "man", "male", "boy", "boys"]) and not is_women_query
    
    is_prod_women = "women" in prod_id or "women" in name or "women" in category
    is_prod_men = "men" in prod_id or "men" in name or "men" in category
    
    score = min(1.0, matches / (len(query_tokens) * 1.2))
    
    if is_women_query and is_prod_men:
        score *= 0.2
    elif is_men_query and is_prod_women:
        score *= 0.2
    elif (is_women_query and is_prod_women) or (is_men_query and is_prod_men):
        score = min(1.0, score * 1.3)
        
    return score

class TextSearchService:
    def __init__(self, image_search_service: ImageSearchService = None):
        self.last_timer = None
        if image_search_service is None:
            try:
                from backend.routes.image_search import get_search_service
                self.image_search_service = get_search_service()
            except Exception:
                self.image_search_service = ImageSearchService()
        else:
            self.image_search_service = image_search_service

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the product catalog using a robust hybrid approach combining
        CLIP text embeddings with metadata keyword & category fallback for cloud compatibility.
        """
        timer = SearchPerformanceTimer()
        timer.start_total()
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if self.image_search_service.index is None or self.image_search_service.metadata is None:
            self.image_search_service.load_index_and_metadata()

        query_tokens = [
            w for w in re.findall(r'\w+', query.lower()) 
            if len(w) > 1 and w not in STOP_WORDS
        ]

        scored_results = []
        
        # 1. Vector similarity search via CLIP text embedding
        try:
            timer.start_section()
            query_embedding = get_text_embedding(query)
            timer.stop_embedding()
            
            timer.start_section()
            candidate_count = min(250, self.image_search_service.index.ntotal)
            distances, indices = execute_faiss_search(
                self.image_search_service.index, 
                query_embedding, 
                candidate_count
            )
            timer.stop_faiss()

            candidates = retrieve_product_metadata(
                self.image_search_service.metadata, 
                indices, 
                distances
            )

            is_women_query = any(w in query_tokens for w in ["women", "womens", "woman", "female", "ladies"])
            is_men_query = any(m in query_tokens for m in ["men", "mens", "man", "male"]) and not is_women_query

            for cand in candidates:
                cand_score = cand["similarity_score"]
                keyword_score = compute_keyword_score(query_tokens, cand) if query_tokens else 0.0
                
                prod_id = cand.get("product_id", "").lower()
                name = cand.get("name", "").lower()
                category = cand.get("category", "").lower()
                is_prod_women = "women" in prod_id or "women" in name or "women" in category
                is_prod_men = "men" in prod_id or "men" in name or "men" in category

                # Apply gender filter multiplier to CLIP vector score
                if is_women_query and is_prod_men:
                    cand_score *= 0.5
                elif is_men_query and is_prod_women:
                    cand_score *= 0.5
                elif (is_women_query and is_prod_women) or (is_men_query and is_prod_men):
                    cand_score = min(0.98, cand_score * 1.05)

                if keyword_score > 0:
                    hybrid_score = 0.7 * cand_score + 0.3 * keyword_score
                else:
                    hybrid_score = cand_score
                    
                cand_copy = cand.copy()
                cand_copy["similarity_score"] = float(round(hybrid_score, 4))
                scored_results.append(cand_copy)
        except Exception as e:
            print(f"Notice: Vector embedding search bypassed due to cloud memory constraint: {e}")

        # 2. Metadata keyword and category alignment fallback/enhancement
        all_meta = self.image_search_service.metadata or []
        seen_ids = {r["product_id"] for r in scored_results}
        
        extra_matches = []
        for p in all_meta:
            if p["product_id"] in seen_ids:
                continue
            kw_score = compute_keyword_score(query_tokens, p) if query_tokens else 0.0
            if kw_score > 0.3:
                p_copy = p.copy()
                p_copy["similarity_score"] = float(round(0.55 + 0.25 * kw_score, 4))
                extra_matches.append(p_copy)

        extra_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        scored_results.extend(extra_matches)
        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        final_results = scored_results[:top_k]
        
        timer.stop_total()
        self.last_timer = timer
        
        return final_results
