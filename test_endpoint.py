import os
import sys
import requests

def test_api_endpoint():
    print("=== NovaLens AI API Endpoint Verification Test ===")
    
    url = "http://127.0.0.1:8000/api/image-search"
    image_path = os.path.join("data", "DeepFashion", "MEN", "Denim", "id_00000080", "01_1_front.jpg")
    if not os.path.exists(image_path):
        image_path = os.path.join("data", "DeepFashion", "img_highres", "MEN", "Denim", "id_00000080", "01_1_front.jpg")
    
    if not os.path.exists(image_path):
        print(f"[FAIL] Test image not found at: {image_path}")
        return False
        
    print(f"Sending visual search request to {url} with image '{image_path}'...")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": ("01_1_front.jpg", f, "image/jpeg")}
            response = requests.post(url, files=files)
            
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[FAIL] Endpoint returned error: {response.text}")
            return False
            
        results = response.json()
        print(f"[OK] Endpoint responded successfully. Returned {len(results)} products.")
        
        for rank, product in enumerate(results, 1):
            print(f"  Rank {rank}: {product['product_id']} | {product['name']} | Match: {product['similarity_score']*100:.2f}% | Path: {product['image_path']}")
            
        if len(results) == 0:
            print("[FAIL] Empty search results returned.")
            return False
            
        # Top match validation
        top_match = results[0]
        if top_match['product_id'] == "MEN_Denim_id_00000080" and top_match['similarity_score'] > 0.99:
            print("\n=== Endpoint HTTP Request Verification PASSED! ===")
            return True
        else:
            print(f"[FAIL] Expected top match MEN_Denim_id_00000080 with ~100% score. Got {top_match['product_id']} with {top_match['similarity_score']*100:.2f}%")
            return False
            
    except Exception as e:
        print(f"[FAIL] HTTP request failed: {e}")
        return False

if __name__ == "__main__":
    import time
    # Small sleep to ensure uvicorn is fully bound and listening
    time.sleep(2)
    success = test_api_endpoint()
    sys.exit(0 if success else 1)
