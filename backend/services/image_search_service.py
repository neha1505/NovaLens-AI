import os
import sys
import pickle
import numpy as np
import faiss
from PIL import Image
from typing import List, Dict, Any

# Add base directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.clip.image_embedding import get_image_embedding

class ImageSearchService:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.index_path = os.path.join(self.base_dir, "vector_store", "image_faiss.index")
        self.metadata_path = os.path.join(self.base_dir, "vector_store", "image_metadata.pkl")
        
        self.index = None
        self.metadata = None
        # Attempt loading on initialization; backend main handles error checking gracefully
        try:
            self.load_index_and_metadata()
        except Exception as e:
            print(f"Warning: Initial index load failed: {e}. Will retry on search.")

    def load_index_and_metadata(self):
        """Loads FAISS index and product metadata pickle."""
        if not os.path.exists(self.index_path):
            raise RuntimeError(
                f"FAISS index file not found at: {self.index_path}. "
                "Please run 'python vector_store/build_image_index.py' to build the index."
            )
        if not os.path.exists(self.metadata_path):
            raise RuntimeError(
                f"Metadata file not found at: {self.metadata_path}. "
                "Please run 'python vector_store/build_image_index.py' to generate metadata."
            )
        
        try:
            print(f"Loading FAISS index from {self.index_path}...")
            self.index = faiss.read_index(self.index_path)
            
            print(f"Loading metadata from {self.metadata_path}...")
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
                
            print(f"Image search service loaded successfully with {len(self.metadata)} products.")
        except Exception as e:
            print(f"Error loading FAISS index or metadata: {e}")
            raise RuntimeError(f"Failed to initialize search service: {e}")

    def search(self, image: Image.Image, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index for the top_k most similar products.
        """
        if self.index is None or self.metadata is None:
            self.load_index_and_metadata()

        # 1. Generate query embedding (normalized)
        query_embedding = get_image_embedding(image)
        
        # 2. Reshape for FAISS search (needs 2D array: shape (1, dimension))
        query_vector = np.expand_dims(query_embedding, axis=0).astype('float32')

        # 3. Perform similarity search
        k = min(top_k, self.index.ntotal)
        if k == 0:
            return []

        # distances: shape (1, k), indices: shape (1, k)
        distances, indices = self.index.search(query_vector, k)

        # 4. Map index back to product metadata
        results = []
        for rank in range(k):
            idx = indices[0][rank]
            score = float(distances[0][rank]) # Cosine similarity score
            
            # FAISS returns -1 index if not enough matches are found
            if idx == -1 or idx >= len(self.metadata):
                continue
                
            product_info = self.metadata[idx].copy()
            # Clip similarity score to be between 0.0 and 1.0
            product_info["similarity_score"] = max(0.0, min(1.0, score))
            results.append(product_info)

        return results
