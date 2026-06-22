import os
import sys
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

base_dir = r"c:\Users\nehas\.gemini\antigravity-ide\scratch\NovaLens-AI"
sys.path.append(base_dir)

from backend.main import app

def test_migration():
    print("=== NovaLens AI Dataset Migration Verification ===")
    
    # 1. Check folder assets existence
    processed_dir = os.path.join(base_dir, "data", "processed")
    csv_path = os.path.join(processed_dir, "products.csv")
    embeddings_path = os.path.join(processed_dir, "image_embeddings.npy")
    index_path = os.path.join(processed_dir, "faiss.index")

    print("\n1. Verifying data asset existence...")
    if not os.path.exists(csv_path):
        print(f"[FAIL] products.csv not found at: {csv_path}")
        return False
    print(f"[OK] products.csv found. Size: {os.path.getsize(csv_path)} bytes.")

    if not os.path.exists(embeddings_path):
        print(f"[FAIL] image_embeddings.npy not found at: {embeddings_path}")
        return False
    print(f"[OK] image_embeddings.npy found. Size: {os.path.getsize(embeddings_path)} bytes.")

    if not os.path.exists(index_path):
        print(f"[FAIL] faiss.index not found at: {index_path}")
        return False
    print(f"[OK] faiss.index found. Size: {os.path.getsize(index_path)} bytes.")

    # Load metadata to find a valid sample ID
    import csv
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        products = list(reader)
    if not products:
        print("[FAIL] products.csv is empty")
        return False
    
    sample_prod = products[0]
    sample_id = sample_prod["product_id"]
    sample_image_rel = sample_prod["primary_image"]
    sample_image_abs = os.path.join(base_dir, "data", sample_image_rel)

    print(f"[OK] Total products registered in CSV: {len(products)}")
    print(f"[OK] Sample product: ID={sample_id}, Name='{sample_prod['product_name']}'")
    print(f"[OK] Sample image path: {sample_image_rel}")

    client = TestClient(app)

    # 2. Test GET /api/products/{id}
    print(f"\n2. Testing GET /api/products/{sample_id}...")
    response = client.get(f"/api/products/{sample_id}")
    if response.status_code != 200:
        print(f"[FAIL] Status code: {response.status_code}, Details: {response.text}")
        return False
    data = response.json()
    print("[OK] Product details response:")
    print(data)
    
    # 3. Test GET /api/products/{id}/similar
    print(f"\n3. Testing GET /api/products/{sample_id}/similar...")
    response = client.get(f"/api/products/{sample_id}/similar")
    if response.status_code != 200:
        print(f"[FAIL] Status code: {response.status_code}, Details: {response.text}")
        return False
    similar = response.json()
    print(f"[OK] Returned {len(similar)} recommendations. First recommendation:")
    print(similar[0] if similar else "Empty list!")
    if len(similar) == 0:
        print("[FAIL] Empty recommendations list.")
        return False

    # 4. Test POST /api/text-search
    print("\n4. Testing POST /api/text-search for 'shirt'...")
    response = client.post("/api/text-search", json={"query": "shirt"})
    if response.status_code != 200:
        print(f"[FAIL] Status code: {response.status_code}, Details: {response.text}")
        return False
    results = response.json()
    print(f"[OK] Returned {len(results)} matches. Top match:")
    print(results[0] if results else "Empty list!")

    # 5. Test POST /api/image-search
    print("\n5. Testing POST /api/image-search...")
    if not os.path.exists(sample_image_abs):
        print(f"[FAIL] Image file not found for visual search test at: {sample_image_abs}")
        return False
        
    with open(sample_image_abs, "rb") as f:
        files = {"file": (os.path.basename(sample_image_abs), f, "image/jpeg")}
        response = client.post("/api/image-search", files=files)
        
    if response.status_code != 200:
        print(f"[FAIL] Status code: {response.status_code}, Details: {response.text}")
        return False
    image_results = response.json()
    print(f"[OK] Visual search responded successfully. Top match:")
    print(image_results[0] if image_results else "Empty list!")
    
    # Verify that the query image matches itself first (since it is in the database)
    if image_results and image_results[0]["product_id"] == sample_id:
        print("[OK] Visual search exact match validation succeeded.")
    else:
        print(f"[WARN] Expected top match '{sample_id}', got '{image_results[0]['product_id'] if image_results else 'None'}'")

    print("\n=== Dataset Migration Verification PASSED! ===")
    return True

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)
