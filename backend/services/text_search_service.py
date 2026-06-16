import os
import sys
from typing import List, Dict, Any

# Ensure base directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.image_search_service import ImageSearchService
from ml.clip.text_embedding import get_text_embedding
from backend.utils.search_helpers import (
    execute_faiss_search,
    retrieve_product_metadata,
    SearchPerformanceTimer
)

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
        Searches the FAISS index for the top_k most similar products based on a text query.
        Includes performance timing instrumentation.
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
        
        # 2. Perform similarity search in FAISS
        timer.start_section()
        distances, indices = execute_faiss_search(
            self.image_search_service.index, 
            query_embedding, 
            top_k
        )
        timer.stop_faiss()

        # 3. Map index back to product metadata
        results = retrieve_product_metadata(
            self.image_search_service.metadata, 
            indices, 
            distances
        )
        
        timer.stop_total()
        self.last_timer = timer
        
        print(f"[METRICS] Text Search: Total={timer.total_search_time:.4f}s | "
              f"Embedding={timer.embedding_generation_time:.4f}s | FAISS={timer.faiss_search_time:.4f}s")
        
        return results
