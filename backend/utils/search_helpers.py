import os
import time
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any

class SearchPerformanceTimer:
    """
    Utility class to capture performance timings for search pipelines,
    including embedding generation, FAISS querying, and overall search latency.
    """
    def __init__(self):
        self.embedding_generation_time = 0.0
        self.faiss_search_time = 0.0
        self.total_search_time = 0.0
        self._start_time = None
        self._section_start = None

    def start_total(self):
        self._start_time = time.perf_counter()

    def stop_total(self):
        if self._start_time:
            self.total_search_time = round(time.perf_counter() - self._start_time, 4)

    def start_section(self):
        self._section_start = time.perf_counter()

    def stop_embedding(self):
        if self._section_start:
            self.embedding_generation_time = round(time.perf_counter() - self._section_start, 4)
            self._section_start = None

    def stop_faiss(self):
        if self._section_start:
            self.faiss_search_time = round(time.perf_counter() - self._section_start, 4)
            self._section_start = None

def load_faiss_index(index_path: str):
    """Loads a FAISS index from the specified local path."""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index file not found at: {index_path}")
    try:
        return faiss.read_index(index_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read FAISS index from {index_path}: {e}")

def load_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """Loads product catalog metadata from a serialized pickle file."""
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found at: {metadata_path}")
    try:
        with open(metadata_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load metadata from {metadata_path}: {e}")

def execute_faiss_search(index, query_vector: np.ndarray, top_k: int):
    """
    Queries the FAISS index with a 2D float32 vector and returns
    distances and indices for the closest top_k matches.
    """
    k = min(top_k, index.ntotal)
    if k <= 0:
        return np.array([]), np.array([])
    # FAISS expects float32 2D array of shape (1, dimension)
    if query_vector.ndim == 1:
        query_vector = np.expand_dims(query_vector, axis=0)
    query_vector = query_vector.astype('float32')
    
    distances, indices = index.search(query_vector, k)
    return distances[0], indices[0]

def retrieve_product_metadata(
    metadata: List[Dict[str, Any]], 
    indices: np.ndarray, 
    distances: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Maps list indices back to product metadata records, formats similarity scores
    in [0.0, 1.0], and returns a ranked list.
    """
    results = []
    for score, idx in zip(distances, indices):
        if idx == -1 or idx >= len(metadata):
            continue
        product_info = metadata[idx].copy()
        # Cosine similarity clip
        product_info["similarity_score"] = float(max(0.0, min(1.0, score)))
        results.append(product_info)
    return results
