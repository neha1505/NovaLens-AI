from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    from backend.routes.text_search import get_text_search_service
    from backend.services.text_search_service import TextSearchService
    from backend.services.llm_service import LLMService
except ImportError:
    from routes.text_search import get_text_search_service
    from services.text_search_service import TextSearchService
    from services.llm_service import LLMService

router = APIRouter()

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant' / 'model'")
    content: str = Field(..., description="Message content")

class AssistantChatRequest(BaseModel):
    message: str = Field(..., description="The user's direct chat prompt")
    history: List[ChatMessage] = Field(default=[], description="Previous conversational history")
    recently_viewed: List[str] = Field(default=[], description="Product IDs of items recently viewed in browser")

class ProductCitation(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    price: float
    image_path: str

class AssistantChatResponse(BaseModel):
    response: str
    products: List[ProductCitation]

@router.post("/assistant/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    request: AssistantChatRequest,
    search_service: TextSearchService = Depends(get_text_search_service)
):
    """
    RAG Assistant Chat Endpoint.
    Performs FAISS retrieval over the fashion catalog, constructs context prompts,
    instructs the LLM, and returns styling advice with matching product details.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        # Ensure metadata and index are pre-loaded
        if search_service.image_search_service.index is None or search_service.image_search_service.metadata is None:
            search_service.image_search_service.load_index_and_metadata()

        # 1. Retrieve products via TextSearchService (top_k=6 for concise context)
        # Handle cases where the query is short or needs expansion by using user query
        retrieved_products = []
        try:
            retrieved_products = search_service.search(request.message.strip(), top_k=6)
        except Exception as e:
            # Log error and keep list empty (graceful fallback)
            print(f"RAG search error: {e}")

        # Ensure the most recently viewed product is in the retrieved_products list (grounding for styling queries)
        target_product = None
        if request.recently_viewed:
            last_viewed_id = request.recently_viewed[0]
            exists = any(p["product_id"] == last_viewed_id for p in retrieved_products)
            if not exists:
                for p in search_service.image_search_service.metadata:
                    if p.get("product_id") == last_viewed_id:
                        retrieved_products.insert(0, p)
                        target_product = p
                        break
            else:
                for p in retrieved_products:
                    if p["product_id"] == last_viewed_id:
                        target_product = p
                        break

        # 2. Extract metadata for user's recently viewed products for personalization context
        viewed_products_metadata = []
        if request.recently_viewed:
            viewed_ids_set = set(request.recently_viewed[:5])  # Cap to top 5
            for p in search_service.image_search_service.metadata:
                if p.get("product_id") in viewed_ids_set:
                    viewed_products_metadata.append(p)

        # 3. Build RAG system and prompt context
        system_instruction = (
            "You are the NovaLens AI Fashion Assistant, an expert, stylish, and supportive fashion shopping advisor. "
            "Your role is to understand user fashion requests, suggest outfits, style tips, and recommend products from the catalog. "
            "\n\n"
            "STRICT RULES:\n"
            "1. Grounding: You must ONLY recommend products that are explicitly provided in the 'RETRIVED PRODUCTS FROM CATALOG' list below. "
            "Do NOT recommend, invent, or mention products that are not in the list. "
            "If no products are in the list, state that you couldn't find strong matches in the catalog, but offer general style suggestions.\n"
            "2. Citation Format: When recommending a product, refer to it using markdown link format: `[Product Name](/product/product_id)` "
            "and also display its ID. For example: 'We recommend the **[Black Casual Hoodie](/product/MEN_Denim_id_00000080)** (ID: `MEN_Denim_id_00000080`) because it matches...'\n"
            "3. Personalization: If details are provided in 'USER RECENTLY VIEWED', reference them naturally (e.g. 'Since you recently explored denim...').\n"
            "4. Outfit/Styling Queries: If the user asks for outfit suggestions, styling ideas (e.g., 'Style this jacket', 'What should I wear with...', 'Create a casual outfit', 'Suggest a winter look'), you must structure your response to include:\n"
            "   - **Outfit Name**: A stylish title for the look (e.g., 'Everyday College Wear' or 'Streetwear Edge Outfit')\n"
            "   - **Style**: Specify the style (Casual, College, Streetwear, Smart Casual, Winter Wear, Minimalist, or Everyday Wear)\n"
            "   - **Explanation**: A brief styling rationale explaining why these items work together.\n"
            "   - **Suggested Pieces**: An itemized list of suggested items from the catalog (referencing them using the markdown link format and showing the product ID).\n"
            "5. OCCASION/SEASON: Provide detailed fashion logic (why this matches college, winter, streetwear, etc.). Keep the tone premium and stylish."
        )

        # Build context segment
        context = []
        if viewed_products_metadata:
            context.append("--- USER RECENTLY VIEWED PRODUCTS ---")
            for p in viewed_products_metadata:
                context.append(f"- Name: {p['name']} | ID: {p['product_id']} | Category: {p['category']} | Price: ₹{p['price']}")
            context.append("")

        context.append("--- RETRIEVED PRODUCTS FROM CATALOG ---")
        if retrieved_products:
            for p in retrieved_products:
                context.append(
                    f"- Product Name: {p['name']}\n"
                    f"  Product ID: {p['product_id']}\n"
                    f"  Category: {p['category']}\n"
                    f"  Price: ₹{p['price']}\n"
                    f"  Description: {p.get('description', 'No description available.')}\n"
                )
        else:
            context.append("No matching catalog items retrieved.")

        context_str = "\n".join(context)

        # 4. Construct messages payload
        llm_messages = []
        for h in request.history:
            # Normalize role strings
            role = "model" if h.role in ("assistant", "model") else "user"
            llm_messages.append({"role": role, "content": h.content})

        # Append current user prompt containing retrieved context
        user_content = (
            f"Here is context about the fashion products matching the user's request:\n\n"
            f"{context_str}\n\n"
            f"User Question: {request.message}"
        )
        llm_messages.append({"role": "user", "content": user_content})

        # 5. Call LLM Service
        llm_service = LLMService()
        response_text = await llm_service.generate_response(
            system_instruction=system_instruction,
            messages=llm_messages,
            temperature=0.7
        )

        # 6. Parse LLM response to identify cited product IDs and build matching citations list
        import re
        cited_pids = set(re.findall(r'[A-Za-z0-9_]+_id_[0-9]+', response_text))
        
        matched_products = []
        if cited_pids:
            for p in search_service.image_search_service.metadata:
                if p["product_id"] in cited_pids:
                    matched_products.append(ProductCitation(
                        product_id=p["product_id"],
                        name=p["name"],
                        category=p["category"],
                        description=p.get("description", ""),
                        price=p["price"],
                        image_path=p["image_path"]
                    ))

        # Fallback to retrieved products if no specific catalog IDs were cited
        if not matched_products:
            for p in retrieved_products:
                matched_products.append(ProductCitation(
                    product_id=p["product_id"],
                    name=p["name"],
                    category=p["category"],
                    description=p.get("description", ""),
                    price=p["price"],
                    image_path=p["image_path"]
                ))

        return AssistantChatResponse(
            response=response_text,
            products=matched_products
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating Assistant chat response: {str(e)}"
        )
