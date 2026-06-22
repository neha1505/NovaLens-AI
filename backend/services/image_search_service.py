import os
import sys
from PIL import Image
from typing import List, Dict, Any

# Add base directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.clip.image_embedding import get_image_embedding
from backend.utils.search_helpers import (
    load_faiss_index,
    load_metadata,
    execute_faiss_search,
    retrieve_product_metadata,
    SearchPerformanceTimer
)

class ImageSearchService:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.index_path = os.path.join(self.base_dir, "data", "processed", "faiss.index")
        self.metadata_path = os.path.join(self.base_dir, "data", "processed", "products.csv")
        
        self.index = None
        self.metadata = None
        self.last_timer = None
        
        # Attempt loading on initialization; backend main handles error checking gracefully
        try:
            self.load_index_and_metadata()
        except Exception as e:
            print(f"Warning: Initial index load failed: {e}. Will retry on search.")

    def load_index_and_metadata(self):
        """Loads FAISS index and product metadata pickle using shared helpers."""
        try:
            self.index = load_faiss_index(self.index_path)
            self.metadata = load_metadata(self.metadata_path)
            print(f"Image search service loaded successfully with {len(self.metadata)} products.")
        except FileNotFoundError as e:
            raise RuntimeError(
                "Search index database files are missing. Please build the FAISS index "
                "by running 'python vector_store/build_image_index.py' before executing searches."
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize search database: {e}") from e

    def search(self, image: Image.Image, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index for the top_k most similar products.
        Includes performance timing instrumentation.
        """
        timer = SearchPerformanceTimer()
        timer.start_total()
        
        if self.index is None or self.metadata is None:
            self.load_index_and_metadata()

        # 1. Generate query embedding (normalized)
        timer.start_section()
        query_embedding = get_image_embedding(image)
        timer.stop_embedding()
        
        # 2. Perform similarity search
        timer.start_section()
        distances, indices = execute_faiss_search(self.index, query_embedding, top_k)
        timer.stop_faiss()

        # 3. Map index back to product metadata
        results = retrieve_product_metadata(self.metadata, indices, distances)
        
        timer.stop_total()
        self.last_timer = timer
        
        print(f"[METRICS] Image Search: Total={timer.total_search_time:.4f}s | "
              f"Embedding={timer.embedding_generation_time:.4f}s | FAISS={timer.faiss_search_time:.4f}s")
        
        return results
