import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure base directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestMultimodalSearchEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_image_path = os.path.join("data", "fashion", "images", "15970.jpg")
        
        # Fallback path if data_dir structure differs
        if not os.path.exists(cls.sample_image_path):
            cls.sample_image_path = os.path.join("data", "images", "15970.jpg")

    def test_multimodal_endpoint_availability(self):
        """Verify the multimodal endpoint returns a response (checks routing setup)."""
        response = self.client.post("/api/multimodal-search")
        # Empty request should return 400, confirming the endpoint exists and validates inputs
        self.assertEqual(response.status_code, 400)

    def test_multimodal_search_image_only(self):
        """Test multimodal search with an image upload but no text modifier query."""
        self.assertTrue(os.path.exists(self.sample_image_path), f"Test image not found at {self.sample_image_path}")
        
        with open(self.sample_image_path, "rb") as img_file:
            files = {"image": ("15970.jpg", img_file, "image/jpeg")}
            data = {"image_weight": "1.0"} # Full image weight
            response = self.client.post("/api/multimodal-search", files=files, data=data)
            
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify schema
        first = results[0]
        self.assertIn("product_id", first)
        self.assertIn("similarity_score", first)
        self.assertEqual(first["product_id"], "15970") # Top match should be itself

    def test_multimodal_search_text_only(self):
        """Test multimodal search with query text but no uploaded image."""
        data = {
            "query_text": "red sneakers",
            "image_weight": "0.0" # Text focus
        }
        response = self.client.post("/api/multimodal-search", data=data)
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_multimodal_search_fused(self):
        """Test multimodal search fusing image and text modifiers simultaneously."""
        self.assertTrue(os.path.exists(self.sample_image_path))
        
        with open(self.sample_image_path, "rb") as img_file:
            files = {"image": ("15970.jpg", img_file, "image/jpeg")}
            data = {
                "query_text": "similar but red color",
                "image_weight": "0.6" # Balance visual and text
            }
            response = self.client.post("/api/multimodal-search", files=files, data=data)
            
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Schema checks
        first = results[0]
        self.assertIn("product_id", first)
        self.assertIn("name", first)
        self.assertIn("similarity_score", first)

    def test_multimodal_search_invalid_image(self):
        """Verify that uploading an invalid/corrupted file results in HTTP 400."""
        files = {"image": ("bad.txt", b"not-an-image-file-contents", "text/plain")}
        data = {"query_text": "casual shoes"}
        response = self.client.post("/api/multimodal-search", files=files, data=data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_multimodal_search_empty_request(self):
        """Verify that sending a request with neither image nor text query returns HTTP 400."""
        data = {"image_weight": "0.5"}
        response = self.client.post("/api/multimodal-search", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_multimodal_search_invalid_weight(self):
        """Verify that sending a weight outside [0.0, 1.0] returns HTTP 400."""
        data = {"query_text": "shoes", "image_weight": "1.5"}
        response = self.client.post("/api/multimodal-search", data=data)
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
