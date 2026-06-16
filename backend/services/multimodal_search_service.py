import os
import sys
import numpy as np
from PIL import Image
from typing import List, Dict, Any

# Ensure base directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.image_search_service import ImageSearchService
from ml.clip.image_embedding import get_image_embedding
from ml.clip.text_embedding import get_text_embedding
from backend.utils.search_helpers import (
    execute_faiss_search,
    retrieve_product_metadata,
    SearchPerformanceTimer
)

class MultimodalSearchService:
    def __init__(self, image_search_service: ImageSearchService = None):
        """
        Initializes the MultimodalSearchService, reusing the shared FAISS database
        and metadata mapping to optimize performance.
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

    def search(
        self, 
        image: Image.Image = None, 
        query_text: str = None, 
        image_weight: float = 0.7, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Performs a multimodal similarity lookup by fusing visual and textual query embeddings.
        Includes performance timing metrics.
        """
        timer = SearchPerformanceTimer()
        timer.start_total()
        
        if image is None and (not query_text or not query_text.strip()):
            raise ValueError("At least one input (image or query text) is required for multimodal search.")
        if not (0.0 <= image_weight <= 1.0):
            raise ValueError("Image weight must be between 0.0 and 1.0.")

        # Ensure index and metadata are loaded in the underlying service
        if self.image_search_service.index is None or self.image_search_service.metadata is None:
            self.image_search_service.load_index_and_metadata()

        timer.start_section()
        
        # 1. Generate image embedding if present
        image_embedding = None
        if image is not None:
            image_embedding = get_image_embedding(image)

        # 2. Generate text embedding if present
        text_embedding = None
        if query_text and query_text.strip():
            text_embedding = get_text_embedding(query_text)

        # 3. Fuse embeddings linearly
        if image_embedding is not None and text_embedding is not None:
            text_weight = 1.0 - image_weight
            combined_embedding = image_weight * image_embedding + text_weight * text_embedding
        elif image_embedding is not None:
            combined_embedding = image_embedding
        else:
            combined_embedding = text_embedding

        # 4. Normalize the fused vector (L2 norm)
        norm = np.linalg.norm(combined_embedding)
        if norm > 0:
            combined_embedding = combined_embedding / norm
        else:
            raise RuntimeError("Linear embedding fusion resulted in a zero vector.")
            
        timer.stop_embedding()

        # 5. Perform similarity search in FAISS
        timer.start_section()
        distances, indices = execute_faiss_search(
            self.image_search_service.index, 
            combined_embedding, 
            top_k
        )
        timer.stop_faiss()

        # 6. Map index back to product metadata
        results = retrieve_product_metadata(
            self.image_search_service.metadata, 
            indices, 
            distances
        )
        
        timer.stop_total()
        self.last_timer = timer
        
        print(f"[METRICS] Multimodal Search: Total={timer.total_search_time:.4f}s | "
              f"Embedding={timer.embedding_generation_time:.4f}s | FAISS={timer.faiss_search_time:.4f}s")
        
        return results
