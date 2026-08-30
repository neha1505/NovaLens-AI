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

STOP_WORDS = {"a", "an", "the", "in", "on", "at", "for", "with", "and", "or", "of", "to", "is", "are", "women", "womens", "men", "mens"}

CATEGORY_SYNONYMS = {
    "dress": ["dresses", "dress"],
    "dresses": ["dresses", "dress"],
    "shirt": ["blouses_shirts", "shirts_polos", "shirt"],
    "shirts": ["blouses_shirts", "shirts_polos", "shirt"],
    "jacket": ["jackets_vests", "jackets_coats", "jacket"],
    "jackets": ["jackets_vests", "jackets_coats", "jacket"],
    "jeans": ["denim", "pants", "jeans"],
    "shorts": ["shorts"],
    "skirt": ["skirts", "skirt"],
    "skirts": ["skirts", "skirt"],
    "coat": ["jackets_coats", "coat"],
    "coats": ["jackets_coats", "coat"],
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
    
    matches = 0.0
    
    for token in query_tokens:
        synonyms = CATEGORY_SYNONYMS.get(token, [token])
        if any(syn in category for syn in synonyms) or any(syn in name for syn in synonyms):
            matches += 1.5
        elif token in name:
            matches += 1.0
        elif token in desc:
            matches += 0.5
            
    return min(1.0, matches / (len(query_tokens) * 1.2))

class TextSearchService:
    def __init__(self, image_search_service: ImageSearchService = None):
        """
        Initializes the TextSearchService, reusing the existing loaded FAISS index
        and metadata mapping to conserve memory.
        """
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
        Searches the product catalog using a hybrid approach combining CLIP text-image
        embeddings with text metadata relevance scoring.
        """
        timer = SearchPerformanceTimer()
        timer.start_total()
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        # Ensure index and metadata are loaded in the underlying service
        if self.image_search_service.index is None or self.image_search_service.metadata is None:
            self.image_search_service.load_index_and_metadata()

        # 1. Generate text query embedding (normalized 512-d vector)
        timer.start_section()
        query_embedding = get_text_embedding(query)
        timer.stop_embedding()
        
        # 2. Perform candidate search in FAISS
        timer.start_section()
        candidate_count = min(250, self.image_search_service.index.ntotal)
        distances, indices = execute_faiss_search(
            self.image_search_service.index, 
            query_embedding, 
            candidate_count
        )
        timer.stop_faiss()

        # 3. Map index back to product metadata candidates
        candidates = retrieve_product_metadata(
            self.image_search_service.metadata, 
            indices, 
            distances
        )

        query_tokens = [
            w for w in re.findall(r'\w+', query.lower()) 
            if len(w) > 1 and w not in STOP_WORDS
        ]

        # 4. Compute hybrid scores
        scored_results = []
        for cand in candidates:
            raw_clip_sim = cand["similarity_score"]
            visual_score = calibrate_similarity_score(raw_clip_sim)
            keyword_score = compute_keyword_score(query_tokens, cand) if query_tokens else 0.0
            
            if keyword_score > 0:
                hybrid_score = 0.5 * visual_score + 0.5 * min(1.0, 0.70 + 0.30 * keyword_score)
            else:
                hybrid_score = visual_score
                
            cand_copy = cand.copy()
            cand_copy["similarity_score"] = float(round(hybrid_score, 4))
            scored_results.append(cand_copy)

        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Check catalog for explicit keyword matches if top candidates lack direct text matches
        if query_tokens and (not scored_results or scored_results[0]["similarity_score"] < 0.75):
            all_meta = self.image_search_service.metadata
            extra_matches = []
            for p in all_meta:
                kw_score = compute_keyword_score(query_tokens, p)
                if kw_score >= 0.5:
                    p_copy = p.copy()
                    p_copy["similarity_score"] = float(round(0.80 + 0.15 * kw_score, 4))
                    extra_matches.append(p_copy)
            
            extra_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            seen_ids = {r["product_id"] for r in scored_results}
            for em in extra_matches:
                if em["product_id"] not in seen_ids:
                    scored_results.append(em)
                    seen_ids.add(em["product_id"])
            
            scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        final_results = scored_results[:top_k]
        
        timer.stop_total()
        self.last_timer = timer
        
        print(f"[METRICS] Text Search: Total={timer.total_search_time:.4f}s | "
              f"Embedding={timer.embedding_generation_time:.4f}s | FAISS={timer.faiss_search_time:.4f}s")
        
        return final_results
