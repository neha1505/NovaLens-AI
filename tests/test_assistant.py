import os
import sys
import unittest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Ensure base directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestAssistantEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @patch("backend.routes.assistant.LLMService.generate_response", new_callable=AsyncMock)
    def test_assistant_chat_success(self, mock_generate_response):
        """Test POST /api/assistant/chat successfully retrieves products and triggers LLM reasoning."""
        mock_generate_response.return_value = (
            "Here is the styling option: [Soft-Knit Rust Denim Jacket](/product/MEN_Denim_id_00000080)."
        )
        
        payload = {
            "message": "Show me a nice rust denim jacket for college",
            "history": [],
            "recently_viewed": ["MEN_Denim_id_00000080"]
        }
        
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("products", data)
        self.assertEqual(data["response"], "Here is the styling option: [Soft-Knit Rust Denim Jacket](/product/MEN_Denim_id_00000080).")
        self.assertIsInstance(data["products"], list)
        
        # Verify that products list contains product records retrieved from FAISS
        self.assertGreater(len(data["products"]), 0)
        first_product = data["products"][0]
        self.assertIn("product_id", first_product)
        self.assertIn("name", first_product)
        self.assertIn("category", first_product)
        self.assertIn("price", first_product)
        self.assertIn("image_path", first_product)

    def test_assistant_chat_empty_message(self):
        """Test POST /api/assistant/chat with an empty message returns 400 Bad Request."""
        payload = {
            "message": "",
            "history": []
        }
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Message content cannot be empty.")

        payload_spaces = {
            "message": "    ",
            "history": []
        }
        response = self.client.post("/api/assistant/chat", json=payload_spaces)
        self.assertEqual(response.status_code, 400)

    @patch("backend.routes.assistant.LLMService.generate_response", new_callable=AsyncMock)
    def test_assistant_chat_multi_turn_history(self, mock_generate_response):
        """Test POST /api/assistant/chat with existing chat history."""
        mock_generate_response.return_value = "Certainly! Try this alternative item."
        
        payload = {
            "message": "Got any other alternatives?",
            "history": [
                {"role": "user", "content": "Show me denim jackets"},
                {"role": "assistant", "content": "Sure, here is the [Soft-Knit Rust Denim Jacket](/product/MEN_Denim_id_00000080)"}
            ],
            "recently_viewed": []
        }
        
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["response"], "Certainly! Try this alternative item.")

if __name__ == "__main__":
    unittest.main()
