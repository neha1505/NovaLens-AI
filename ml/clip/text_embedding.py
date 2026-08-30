import sys
import os
import numpy as np
from ml.clip.clip_loader import CLIPLoader

try:
    import torch
    import clip
except ImportError:
    torch = None
    clip = None

_embedding_cache = {}

def get_text_embedding(text_query: str) -> np.ndarray:
    """
    Generates a normalized 512-dimensional CLIP text embedding for a given text query.
    If torch/clip is unavailable on lightweight cloud instances, raises RuntimeError gracefully.
    """
    if not text_query or not text_query.strip():
        raise ValueError("Search query cannot be empty.")

    query_clean = text_query.strip().lower()
    
    if query_clean in _embedding_cache:
        return _embedding_cache[query_clean].copy()

    loader = CLIPLoader()
    model, _ = loader.get_model_and_preprocess()
    device = loader.get_device()

    if model is None or torch is None or clip is None:
        raise RuntimeError("CLIP PyTorch model not present in lightweight environment.")

    try:
        tokenized_text = clip.tokenize([text_query.strip()]).to(device)
    except Exception as e:
        raise ValueError(f"Failed to tokenize query '{text_query}': {e}")

    with torch.no_grad():
        try:
            text_features = model.encode_text(tokenized_text)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            embedding = text_features.cpu().numpy().flatten()
            _embedding_cache[query_clean] = embedding.copy()
            return embedding
        except Exception as e:
            raise RuntimeError(f"Error encoding text query to CLIP embedding: {e}")
