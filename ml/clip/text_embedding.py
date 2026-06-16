import torch
import clip
import numpy as np
from ml.clip.clip_loader import CLIPLoader

# Optional embedding cache for repeated text queries to save CPU/GPU cycles
_embedding_cache = {}

def get_text_embedding(text_query: str) -> np.ndarray:
    """
    Generates a normalized 512-dimensional CLIP text embedding for a given text query.
    
    Args:
        text_query: The natural language string query.
        
    Returns:
        np.ndarray: A 1D numpy array of size 512 representing the normalized CLIP text embedding.
    """
    if not text_query or not text_query.strip():
        raise ValueError("Search query cannot be empty.")

    query_clean = text_query.strip().lower()
    
    # Check cache first
    if query_clean in _embedding_cache:
        return _embedding_cache[query_clean].copy()

    # Get model and device from singleton loader
    loader = CLIPLoader()
    model, _ = loader.get_model_and_preprocess()
    device = loader.get_device()

    try:
        # Tokenize the text query
        tokenized_text = clip.tokenize([text_query.strip()]).to(device)
    except Exception as e:
        raise ValueError(f"Failed to tokenize query '{text_query}': {e}")

    # Generate text embedding
    with torch.no_grad():
        try:
            # clip model encodes text to features
            text_features = model.encode_text(tokenized_text)
            # L2 Normalize the features (unit norm)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            # Convert to numpy array and flatten/extract vector
            embedding = text_features.cpu().numpy().flatten()
            
            # Save to cache
            _embedding_cache[query_clean] = embedding.copy()
            
            return embedding
        except Exception as e:
            raise RuntimeError(f"Error encoding text query to CLIP embedding: {e}")
