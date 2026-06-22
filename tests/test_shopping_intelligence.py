import os
import sys
import unittest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.services.shopping_intelligence_service import ShoppingIntelligenceService
from backend.services.retailer_connectors import RetailerConnector

class TestShoppingIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.service = ShoppingIntelligenceService()
        cls.mock_product = {
            "product_id": "MEN_Denim_id_00000080",
            "name": "Men's Soft-Knit Rust Denim Jacket",
            "category": "Denim",
            "description": "Rust denim jacket with soft knit detail",
            "price": 4400.0,
            "image_path": "DeepFashion/img_highres/MEN/Denim/id_00000080/01_1_front.jpg"
        }

    def test_connectors_existence(self):
        """Test that all required isolated retailer connectors exist."""
        connectors = self.service.connectors
        self.assertIn("Amazon", connectors)
        self.assertIn("Flipkart", connectors)
        self.assertIn("Myntra", connectors)
        self.assertIn("Ajio", connectors)
        self.assertIn("Tata Cliq", connectors)
        self.assertEqual(len(connectors), 5)
        
        for name, connector in connectors.items():
            self.assertTrue(isinstance(connector, RetailerConnector))

    def test_query_simplification(self):
        """Test that hyper-specific descriptors are stripped from fashion items."""
        # Case A: Men's denim jacket
        q_a = self.service.simplify_query("Men's Soft-Knit Rust Denim Jacket", "Denim")
        self.assertEqual(q_a, "Men Rust Denim Jacket")
        
        # Case B: Women's hoodie
        q_b = self.service.simplify_query("Women's Relaxed Fit Black Hoodie", "Hoodies")
        self.assertEqual(q_b, "Women Relaxed Black Hoodie")

    def test_product_matching_confidence(self):
        """Test that matching confidence calculation correctly accepts or rejects matches."""
        product = {"name": "Black Oversized Hoodie", "category": "Hoodies"}
        
        # Good match
        offer_good = {"product_name": "Comfortable Black Hoodie", "category": "Hoodies"}
        score_good = self.service.calculate_match_confidence(product, offer_good)
        self.assertGreaterEqual(score_good, 0.2)
        
        # Bad match
        offer_bad = {"product_name": "Formal Black Blazer", "category": "Blazers"}
        score_bad = self.service.calculate_match_confidence(product, offer_bad)
        self.assertLess(score_bad, 0.2)

    def test_compare_endpoint_success(self):
        """Test GET /api/products/{product_id}/compare endpoint responds with valid schema."""
        product_id = "MEN_Denim_id_00000080"
        response = self.client.get(f"/api/products/{product_id}/compare")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("ai_analysis", data)
        
        # Check comparison results
        results = data["results"]
        self.assertGreater(len(results), 0)
        for o in results:
            self.assertIn("product_name", o)
            self.assertIn("retailer", o)
            self.assertIn("price", o)
            self.assertIn("shopping_score", o)
            self.assertIsInstance(o["shopping_score"], float)
            self.assertGreaterEqual(o["shopping_score"], 0.0)
            self.assertLessEqual(o["shopping_score"], 1.0)
            self.assertIn("is_best_price", o)
            self.assertIn("is_best_quality", o)
            self.assertIn("is_best_value", o)
            self.assertIn("is_most_popular", o)
            self.assertNotIn("product_url", o)
            self.assertNotIn("url_status", o)

        # Assert results are sorted in descending order of shopping_score
        scores = [o["shopping_score"] for o in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # Check AI recommendations
        analysis = data["ai_analysis"]
        self.assertIn("best_price_explanation", analysis)
        self.assertIn("best_quality_explanation", analysis)
        self.assertIn("best_overall_explanation", analysis)
        self.assertIn("buying_summary", analysis)
        self.assertNotIn("best_price_url", analysis)
        self.assertNotIn("best_price_url_status", analysis)
        self.assertNotIn("best_quality_url", analysis)
        self.assertNotIn("best_quality_url_status", analysis)
        self.assertNotIn("best_overall_url", analysis)
        self.assertNotIn("best_overall_url_status", analysis)


if __name__ == "__main__":
    unittest.main()
