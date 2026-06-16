import os
import sys
import unittest
import time
from fastapi.testclient import TestClient

# Ensure base directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestTextSearchEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_text_search_success(self):
        """Test search with a valid natural language query."""
        response = self.client.post("/api/text-search", json={"query": "blue jeans"})
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify schema field constraints
        for item in results:
            self.assertIn("product_id", item)
            self.assertIn("name", item)
            self.assertIn("category", item)
            self.assertIn("description", item)
            self.assertIn("price", item)
            self.assertIn("similarity_score", item)
            self.assertIn("image_path", item)
            
            self.assertIsInstance(item["product_id"], str)
            self.assertIsInstance(item["name"], str)
            self.assertIsInstance(item["category"], str)
            self.assertIsInstance(item["description"], str)
            self.assertIsInstance(item["price"], (int, float))
            self.assertIsInstance(item["similarity_score"], float)
            self.assertIsInstance(item["image_path"], str)
            
            self.assertTrue(0.0 <= item["similarity_score"] <= 1.0)

    def test_text_search_empty_query(self):
        """Test search with an empty or whitespace query."""
        # Empty string
        response = self.client.post("/api/text-search", json={"query": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())
        
        # Whitespace-only string
        response = self.client.post("/api/text-search", json={"query": "    "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_text_search_latency(self):
        """Test text search response speed is within limits (< 5.0 seconds on CPU)."""
        start = time.perf_counter()
        response = self.client.post("/api/text-search", json={"query": "black backpack"})
        duration = time.perf_counter() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 5.0, f"Search latency too high: {duration:.4f}s")
        print(f"\n[INFO] Text search API latency test: {duration:.4f}s")

if __name__ == "__main__":
    unittest.main()
