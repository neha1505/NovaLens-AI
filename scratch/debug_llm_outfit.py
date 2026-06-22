import os
import sys
import asyncio
import json
import httpx

# Add base directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.image_search_service import ImageSearchService
from backend.services.outfit_service import OutfitService, get_outfit_category_group
from backend.services.llm_service import LLMService

async def main():
    print("Initializing ImageSearchService...")
    s = ImageSearchService()
    s.load_index_and_metadata()
    
    print("Locating product WOMEN_Dresses_id_00007797...")
    product_id = "WOMEN_Dresses_id_00007797"
    target_product = None
    target_idx = -1
    for idx, p in enumerate(s.metadata):
        if p.get("product_id") == product_id:
            target_product = p
            target_idx = idx
            break
            
    if not target_product:
        print("Product not found!")
        return
        
    source_group = get_outfit_category_group(target_product["category"])
    print(f"Product category: {target_product['category']}, Group: {source_group}")
    
    # Get candidates
    o = OutfitService(s)
    target_groups = ["layer", "top"]
    candidates_by_group = {g: [] for g in target_groups}
    
    # Reconstruct vector and search
    query_vector = s.index.reconstruct(target_idx)
    from backend.utils.search_helpers import execute_faiss_search, retrieve_product_metadata
    distances, indices = execute_faiss_search(s.index, query_vector, top_k=400)
    retrieved = retrieve_product_metadata(s.metadata, indices, distances)
    
    for item in retrieved:
        if item.get("product_id") == product_id:
            continue
        grp = get_outfit_category_group(item["category"])
        if grp in candidates_by_group:
            if len(candidates_by_group[grp]) < 12:
                candidates_by_group[grp].append(item)
                
    # Format prompt
    system_instruction = (
        "You are the NovaLens AI Fashion Stylist, a state-of-the-art AI fashion consultant. "
        "Your job is to design a perfect, coherent styled outfit that complements the user's selected product, using only items from the provided list of candidates. "
        "\n\n"
        "CRITICAL RULES:\n"
        "1. GROUNDING: The outfit items you suggest MUST be chosen from the candidates provided. "
        "Never invent fictional products or product IDs. You must only recommend actual candidate product IDs.\n"
        "2. OUTFIT STRUCTURE: Select exactly 2 to 3 complementary products from the candidates list. "
        "For example, if the user product is a jacket, select one Top (T-shirt/shirt) and one Bottom (jeans/pants/shorts).\n"
        "3. OUTFIT STYLES: Select the most appropriate outfit style from the following list:\n"
        "   - Casual\n"
        "   - College\n"
        "   - Streetwear\n"
        "   - Smart Casual\n"
        "   - Winter Wear\n"
        "   - Minimalist\n"
        "   - Everyday Wear\n"
        "4. RESPONSE FORMAT: You must output ONLY a valid JSON object. Do not wrap it in markdown block styles or include any other introductory/conversational text. "
        "All string values in the JSON (especially the 'explanation') MUST be single-line strings. Do not include raw newlines or line breaks inside string values, as this will break JSON parsing.\n"
        "The JSON structure must match exactly:\n"
        "{\n"
        "  \"outfit_name\": \"Brief name of the outfit style (e.g. Streetwear Autumn Vibe)\",\n"
        "  \"style\": \"The selected style name from the supported list above (e.g. Streetwear)\",\n"
        "  \"explanation\": \"A styling explanation explaining why these items work together, color coordination, and occasion logic.\",\n"
        "  \"products\": [\"selected_product_id_1\", \"selected_product_id_2\"]\n"
        "}"
    )

    candidates_context = []
    for grp, items in candidates_by_group.items():
        candidates_context.append(f"--- CANDIDATES FOR {grp.upper()} COMPONENT ---")
        for item in items:
            desc = item.get("description", "No description available.")
            candidates_context.append(
                f"Product ID: {item['product_id']}\n"
                f"Name: {item['name']}\n"
                f"Category: {item['category']}\n"
                f"Price: \u20b9{item['price']}\n"
                f"Description: {desc}\n"
            )
        candidates_context.append("")
    candidates_str = "\n".join(candidates_context)

    prompt = (
        f"Target Product to Style:\n"
        f"Product ID: {target_product['product_id']}\n"
        f"Name: {target_product['name']}\n"
        f"Category: {target_product['category']}\n"
        f"Price: \u20b9{target_product['price']}\n"
        f"Description: {target_product.get('description', '')}\n\n"
        f"{candidates_str}\n"
        f"Personalization Hint: \n\n"
        f"Please generate the outfit recommendations now."
    )

    llm = LLMService()
    # Let's inspect the environment and make direct HTTP call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{llm.gemini_model}:generateContent?key={llm.gemini_key}"
    
    contents = [{
        "role": "user",
        "parts": [{"text": prompt}]
    }]
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096
        }
    }
    
    print(f"Sending request to {llm.gemini_model}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            print(json.dumps(res_json, indent=2))
        else:
            print("Error response:")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
