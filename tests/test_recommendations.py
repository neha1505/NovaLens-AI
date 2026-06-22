import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure base directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestRecommendationsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # We know these IDs exist in DeepFashion based on current catalog structure
        cls.valid_id_1 = "WOMEN_Dresses_id_00007797"
        cls.valid_id_2 = "WOMEN_Dresses_id_00002057"

    def test_recommendations_empty_query(self):
        """Test GET /api/recommendations with no product_ids returns empty list."""
        response = self.client.get("/api/recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        response = self.client.get("/api/recommendations?product_ids=")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        response = self.client.get("/api/recommendations?product_ids=   ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_recommendations_success(self):
        """Test GET /api/recommendations with a valid product ID."""
        response = self.client.get(f"/api/recommendations?product_ids={self.valid_id_1}")
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertIsInstance(results, list)
        # It should return recommendations (max 8)
        self.assertLessEqual(len(results), 8)
        
        # Verify schema field constraints
        for item in results:
            self.assertIn("product_id", item)
            self.assertIn("name", item)
            self.assertIn("category", item)
            self.assertIn("price", item)
            self.assertIn("similarity_score", item)
            self.assertIn("image_path", item)
            
            self.assertIsInstance(item["product_id"], str)
            self.assertIsInstance(item["name"], str)
            self.assertIsInstance(item["category"], str)
            self.assertIsInstance(item["price"], (int, float))
            self.assertIsInstance(item["similarity_score"], float)
            self.assertIsInstance(item["image_path"], str)
            
            # The queried ID should NOT be in the recommendations (exclusion check)
            self.assertNotEqual(item["product_id"], self.valid_id_1)

    def test_recommendations_multiple_ids_and_exclusion(self):
        """Test GET /api/recommendations with multiple product IDs and check exclusion of all inputs."""
        input_ids = f"{self.valid_id_1},{self.valid_id_2}"
        response = self.client.get(f"/api/recommendations?product_ids={input_ids}")
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 8)
        
        # Ensure none of the queried input_ids are returned in recommendations list
        for item in results:
            self.assertNotEqual(item["product_id"], self.valid_id_1)
            self.assertNotEqual(item["product_id"], self.valid_id_2)

if __name__ == "__main__":
    unittest.main()
