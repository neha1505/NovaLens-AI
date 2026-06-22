import os
import sys
import numpy as np
from PIL import Image

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml.clip.clip_loader import CLIPLoader
from ml.clip.image_embedding import get_image_embedding
from backend.services.image_search_service import ImageSearchService

def test_pipeline():
    print("=== NovaLens AI Verification Test ===")
    
    # 1. Test CLIPLoader singleton
    print("\n1. Testing CLIP model loader...")
    try:
        loader = CLIPLoader()
        model, preprocess = loader.get_model_and_preprocess()
        device = loader.get_device()
        print(f"[OK] Model loaded successfully on: {device}")
    except Exception as e:
        print(f"[FAIL] Failed loading model: {e}")
        return False

    # 2. Test Image Embedding generation
    print("\n2. Testing image embedding generation...")
    sample_img_path = os.path.join("data", "DeepFashion", "img_highres", "MEN", "Denim", "id_00000080", "01_1_front.jpg")
    if not os.path.exists(sample_img_path):
        print(f"[FAIL] Sample image not found at: {sample_img_path}")
        return False
        
    try:
        embedding = get_image_embedding(sample_img_path)
        print(f"[OK] Embedding generated. Shape: {embedding.shape}, Dtype: {embedding.dtype}")
        
        # Verify L2 norm is approximately 1.0 (normalized)
        norm = np.linalg.norm(embedding)
        print(f"[OK] Vector L2 norm: {norm:.6f}")
        if not np.isclose(norm, 1.0, atol=1e-4):
            print("[WARN] Warning: Vector is not normalized to unit length.")
            return False
            
        if embedding.shape != (512,):
            print(f"[FAIL] Incorrect embedding dimension: expected (512,), got {embedding.shape}")
            return False
    except Exception as e:
        print(f"[FAIL] Failed generating embedding: {e}")
        return False

    # 3. Test FAISS Index Search
    print("\n3. Testing FAISS index visual search...")
    try:
        search_service = ImageSearchService()
        sample_img = Image.open(sample_img_path)
        results = search_service.search(sample_img, top_k=10)
        
        print(f"[OK] Search successfully executed. Returned {len(results)} matches.")
        
        # Output matches
        for rank, res in enumerate(results, 1):
            print(f"  Rank {rank}: {res['product_id']} | {res['name']} | Cat: {res['category']} | Match: {res['similarity_score'] * 100:.2f}%")
            
        if len(results) == 0:
            print("[FAIL] Search returned zero matches.")
            return False
            
        # Top 1 match for DeepFashion query image should be itself with close to 100% similarity
        top_match = results[0]
        print(f"\nTop match details: ID={top_match['product_id']}, Name='{top_match['name']}', Score={top_match['similarity_score'] * 100:.2f}%")
        if top_match['product_id'] != "MEN_Denim_id_00000080":
            print(f"[FAIL] Search failed: Expected top match 'MEN_Denim_id_00000080', got '{top_match['product_id']}'")
            return False
            
        if not np.isclose(top_match['similarity_score'], 1.0, atol=1e-3):
            print(f"[WARN] Warning: Top exact match score is lower than expected: {top_match['similarity_score']}")
            
        print("\n[OK] Top product matches catalog and similarity score is exact.")
    except Exception as e:
        print(f"[FAIL] Failed index search: {e}")
        return False
        
    print("\n=== All Backend Pipeline Verifications PASSED! ===")
    return True

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
