import os
import sys
import unittest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestOutfitEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_outfit_success(self):
        """Test GET /api/products/{product_id}/outfit returns a valid outfit recommendation."""
        # Use a known product ID from deep fashion dataset
        product_id = "MEN_Denim_id_00000080"
        response = self.client.get(f"/api/products/{product_id}/outfit")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify schema
        self.assertIn("outfit_name", data)
        self.assertIn("style", data)
        self.assertIn("explanation", data)
        self.assertIn("products", data)
        
        self.assertIsInstance(data["products"], list)
        self.assertGreater(len(data["products"]), 0)
        
        # Verify product attributes
        first_product = data["products"][0]
        self.assertIn("product_id", first_product)
        self.assertIn("name", first_product)
        self.assertIn("category", first_product)
        self.assertIn("price", first_product)
        self.assertIn("image_path", first_product)

    def test_get_outfit_not_found(self):
        """Test GET /api/products/{product_id}/outfit with non-existent ID returns 404."""
        invalid_id = "NON_EXISTENT_PRODUCT_ID"
        response = self.client.get(f"/api/products/{invalid_id}/outfit")
        self.assertEqual(response.status_code, 404)

    def test_get_outfit_one_piece_exclusion(self):
        """Test GET /api/products/{product_id}/outfit with a dress product ensures target exclusion."""
        # Use a known dress product ID
        product_id = "WOMEN_Dresses_id_00007797"
        response = self.client.get(f"/api/products/{product_id}/outfit")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("products", data)
        pids = [p["product_id"] for p in data["products"]]
        
        # Verify that the target product itself is NOT included in the recommendations
        self.assertNotIn(product_id, pids)
        self.assertGreater(len(pids), 0)

    @patch("backend.routes.assistant.LLMService.generate_response", new_callable=AsyncMock)
    def test_assistant_outfit_citation_parsing(self, mock_generate_response):
        """Test assistant parsing of product citations in its response text."""
        # Mock LLM to return a response containing a specific product citation
        mock_generate_response.return_value = (
            "You should style this with the **[Men's Soft-Knit Rust Denim Jacket](/product/MEN_Denim_id_00000080)** (ID: `MEN_Denim_id_00000080`)."
        )
        
        payload = {
            "message": "What should I wear with a white t-shirt?",
            "history": [],
            "recently_viewed": []
        }
        
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("response", data)
        self.assertIn("products", data)
        
        # Verify that ONLY the cited product is returned in the products list
        pids = [p["product_id"] for p in data["products"]]
        self.assertIn("MEN_Denim_id_00000080", pids)
        # It shouldn't contain other products that weren't cited
        self.assertEqual(len(data["products"]), 1)

    def test_category_aware_outfit_rules(self):
        """Test that outfit recommendations strictly adhere to category-aware stylist rules."""
        from backend.routes.image_search import get_search_service
        from backend.services.outfit_service import get_stylist_category
        
        search_service = get_search_service()
        if search_service.metadata is None:
            search_service.load_index_and_metadata()
            
        hoodie_id = None
        denim_jacket_id = None
        tshirt_id = None
        dress_id = None
        
        for p in search_service.metadata:
            cat = get_stylist_category(p)
            if cat == "hoodie" and not hoodie_id:
                hoodie_id = p["product_id"]
            elif cat == "denim_jacket" and not denim_jacket_id:
                denim_jacket_id = p["product_id"]
            elif cat == "tshirt" and not tshirt_id:
                tshirt_id = p["product_id"]
            elif cat == "dress" and not dress_id:
                dress_id = p["product_id"]
            
            if hoodie_id and denim_jacket_id and tshirt_id and dress_id:
                break
                
        # 1. Test Hoodie target -> bottom (Jeans/Pants) + layer (Bomber Jacket/Jacket)
        self.assertIsNotNone(hoodie_id, "Could not find a hoodie in metadata")
        response = self.client.get(f"/api/products/{hoodie_id}/outfit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["products"]), 2)
        rec_cats = [get_stylist_category(p) for p in data["products"]]
        self.assertTrue(any(c in ("jeans", "cargo_pants", "joggers", "trousers") for c in rec_cats), f"Hoodie outfit missing bottom category. Recs: {rec_cats}")
        self.assertTrue(any(c in ("bomber_jacket", "denim_jacket", "jacket") for c in rec_cats), f"Hoodie outfit missing layer category. Recs: {rec_cats}")
        
        # 2. Test Denim Jacket target -> top (T-Shirt/Shirt) + bottom (Jeans/Pants)
        self.assertIsNotNone(denim_jacket_id, "Could not find a denim jacket in metadata")
        response = self.client.get(f"/api/products/{denim_jacket_id}/outfit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["products"]), 2)
        rec_cats = [get_stylist_category(p) for p in data["products"]]
        self.assertTrue(any(c in ("tshirt", "shirt") for c in rec_cats), f"Denim Jacket outfit missing top category. Recs: {rec_cats}")
        self.assertTrue(any(c in ("jeans", "cargo_pants", "joggers", "trousers") for c in rec_cats), f"Denim Jacket outfit missing bottom category. Recs: {rec_cats}")
        
        # 3. Test T-Shirt target -> bottom (Cargo Pants/Jeans/Pants/Shorts) + layer (Overshirt/Jacket/Cardigan)
        self.assertIsNotNone(tshirt_id, "Could not find a tshirt in metadata")
        response = self.client.get(f"/api/products/{tshirt_id}/outfit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["products"]), 2)
        rec_cats = [get_stylist_category(p) for p in data["products"]]
        self.assertTrue(any(c in ("cargo_pants", "jeans", "joggers", "trousers", "shorts") for c in rec_cats), f"T-Shirt outfit missing bottom category. Recs: {rec_cats}")
        self.assertTrue(any(c in ("overshirt", "denim_jacket", "jacket", "cardigan") for c in rec_cats), f"T-Shirt outfit missing layer category. Recs: {rec_cats}")

        # 4. Test Dress target -> layer (Cardigan/Jacket/Sweater)
        self.assertIsNotNone(dress_id, "Could not find a dress in metadata")
        response = self.client.get(f"/api/products/{dress_id}/outfit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["products"]), 1)
        rec_cats = [get_stylist_category(p) for p in data["products"]]
        self.assertTrue(any(c in ("cardigan", "jacket", "sweater") for c in rec_cats), f"Dress outfit missing layer category. Recs: {rec_cats}")

    def test_outfit_category_diversity(self):
        """Test that outfit recommendations strictly enforce category diversity and do not return duplicate categories."""
        from backend.routes.image_search import get_search_service
        from backend.services.outfit_service import get_stylist_category
        
        search_service = get_search_service()
        if search_service.metadata is None:
            search_service.load_index_and_metadata()
            
        test_count = 0
        for p in search_service.metadata[:30]:
            product_id = p["product_id"]
            target_cat = get_stylist_category(p)
            
            response = self.client.get(f"/api/products/{product_id}/outfit")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            recs = data.get("products", [])
            rec_cats = [get_stylist_category(item) for item in recs]
            
            # Assert 1: Target category is not in recommended categories
            self.assertNotIn(target_cat, rec_cats, f"Target item {product_id} (category {target_cat}) had recommended products of the same category: {rec_cats}")
            
            # Assert 2: All recommended items have unique stylist categories
            self.assertEqual(len(rec_cats), len(set(rec_cats)), f"Outfit contains duplicate stylist categories: {rec_cats}")
            
            test_count += 1
            if test_count >= 5:
                break

if __name__ == "__main__":
    unittest.main()

