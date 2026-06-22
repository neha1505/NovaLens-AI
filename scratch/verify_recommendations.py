import urllib.request
import json
import sys

def verify_recommendations():
    base_url = "http://127.0.0.1:8000/api/recommendations"
    test_id = "WOMEN_Dresses_id_00007797"
    
    print("--------------------------------------------------")
    print("NovaLens AI - Personalized Recommendations Live Verification")
    print("--------------------------------------------------")
    
    # 1. Test empty request
    try:
        url = base_url
        print(f"Testing URL: {url}")
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        print(f"Empty request response: {data}")
        assert data == [], "Empty query should return an empty list"
        print("[OK] Empty query test passed!")
    except Exception as e:
        print(f"[FAIL] Empty query test failed: {e}")
        sys.exit(1)
        
    # 2. Test request with a valid product ID
    try:
        url = f"{base_url}?product_ids={test_id}"
        print(f"\nTesting URL: {url}")
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        print(f"Recommendations count: {len(data)}")
        
        if len(data) > 0:
            print("First recommendation match:")
            print(json.dumps(data[0], indent=2))
        else:
            print("Warning: No recommendations returned. Make sure the dataset index is loaded.")
            
        assert len(data) <= 8, "Should return at most 8 recommendations"
        
        # Verify exclusion
        for item in data:
            assert item["product_id"] != test_id, f"Viewed item {test_id} should not be in recommendations list!"
            
        print("[OK] Live recommendations request test passed!")
    except Exception as e:
        print(f"[FAIL] Live recommendations request test failed: {e}")
        sys.exit(1)

    print("\n--------------------------------------------------")
    print("All live recommendation tests passed successfully!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    verify_recommendations()
