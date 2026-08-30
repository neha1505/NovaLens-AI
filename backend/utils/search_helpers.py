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

import csv

def load_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """Loads product catalog metadata from a unified CSV file."""
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata CSV file not found at: {metadata_path}")
    try:
        metadata = []
        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert price to float if present
                price_val = 0.0
                if "price" in row:
                    try:
                        price_val = float(row["price"])
                    except ValueError:
                        pass
                
                # Map product_name to name and primary_image to image_path to preserve contract
                product_item = {
                    "product_id": row.get("product_id", ""),
                    "name": row.get("product_name", ""),
                    "category": row.get("category", ""),
                    "description": row.get("description", ""),
                    "price": price_val,
                    "image_path": row.get("primary_image", ""),
                    "all_image_paths": row.get("all_image_paths", "")
                }
                metadata.append(product_item)
            
        return metadata
    except Exception as e:
        raise RuntimeError(f"Failed to load metadata from {metadata_path}: {e}")

def execute_faiss_search(index, query_vector: np.ndarray, top_k: int):
    """
    Queries the FAISS index with a 2D float32 vector and returns
    distances and indices for the closest top_k matches.
    """
    if index is None or not hasattr(index, 'ntotal') or index.ntotal <= 0:
        return np.array([]), np.array([])
    k = min(top_k, index.ntotal)
    if k <= 0:
        return np.array([]), np.array([])
    # FAISS expects float32 2D array of shape (1, dimension)
    if query_vector.ndim == 1:
        query_vector = np.expand_dims(query_vector, axis=0)
    query_vector = query_vector.astype('float32')
    
    distances, indices = index.search(query_vector, k)
    return distances[0], indices[0]

def calibrate_similarity_score(raw_score: float) -> float:
    """
    Calibrates raw CLIP cosine similarity (typically 0.15 - 0.38)
    to a human-intuitive match confidence scale between 0.60 (60%) and 0.98 (98%).
    """
    if raw_score <= 0.0:
        return 0.0
    if raw_score >= 0.99:
        return float(raw_score)
    # Min-max scaling around typical CLIP range [0.18, 0.36]
    calibrated = 0.60 + ((raw_score - 0.18) / (0.36 - 0.18)) * (0.95 - 0.60)
    return float(max(0.50, min(0.98, round(calibrated, 4))))

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
