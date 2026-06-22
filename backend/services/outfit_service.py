import os
import sys
import json
import logging
from typing import List, Dict, Any, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.image_search_service import ImageSearchService
from backend.services.llm_service import LLMService
from backend.utils.search_helpers import execute_faiss_search, retrieve_product_metadata

logger = logging.getLogger("novalens.outfit_service")

# Define category groupings based on the DeepFashion catalog
TOPS = {'tees_tanks', 'shirts_polos', 'sweaters', 'sweatshirts_hoodies', 'blouses_shirts', 'graphic_tees'}
BOTTOMS = {'pants', 'shorts', 'skirts', 'leggings'}
LAYERS = {'jackets_vests', 'jackets_coats', 'cardigans', 'denim'}
ONE_PIECES = {'dresses', 'suiting', 'rompers_jumpsuits'}

def get_outfit_category_group(item: Any) -> str:
    if isinstance(item, str):
        cat_lower = item.lower().replace(" ", "_")
        name = ""
        desc = ""
    else:
        category = item.get("category", "")
        cat_lower = category.lower().replace(" ", "_")
        name = item.get("product_name", item.get("name", "")).lower()
        desc = item.get("description", "").lower()

    # Check name/description keywords first for mixed categories like Denim
    bottom_kws = {"jeans", "pants", "shorts", "skirts", "leggings", "trousers", "joggers"}
    if any(kw in name or kw in desc for kw in bottom_kws):
        return "bottom"
        
    layer_kws = {"jacket", "coat", "vest", "cardigan", "shrug", "blazer", "outerwear"}
    if any(kw in name or kw in desc for kw in layer_kws):
        return "layer"
        
    one_piece_kws = {"dress", "suit", "romper", "jumpsuit", "gown"}
    if any(kw in name or kw in desc for kw in one_piece_kws):
        return "one_piece"
        
    top_kws = {"shirt", "tee", "tank", "blouse", "top", "polo", "sweaters", "sweatshirts", "hoodie"}
    if any(kw in name or kw in desc for kw in top_kws):
        return "top"

    # Fallback to category list matching
    if cat_lower in TOPS:
        return "top"
    elif cat_lower in BOTTOMS:
        return "bottom"
    elif cat_lower in LAYERS:
        return "layer"
    elif cat_lower in ONE_PIECES:
        return "one_piece"
    return "top"  # Default fallback

def sanitize_json_string(s: str) -> str:
    # Replace literal newlines inside double quotes with spaces
    chars = []
    in_quote = False
    escape = False
    for char in s:
        if char == '"' and not escape:
            in_quote = not in_quote
        if char == '\\' and not escape:
            escape = True
        else:
            escape = False
            
        if in_quote and char in ('\n', '\r'):
            chars.append(' ')
        else:
            chars.append(char)
    return "".join(chars)

# Stylist categories and color definitions
NEUTRAL_COLORS = {'black', 'white', 'grey', 'gray', 'charcoal', 'beige', 'cream', 'tan', 'sand', 'khaki'}
VIBRANT_COLORS = {'rust', 'blue', 'navy', 'indigo', 'green', 'olive', 'brown', 'red', 'burgundy', 'maroon', 'pink', 'yellow', 'mustard', 'orange', 'purple', 'teal'}
ALL_COLORS = NEUTRAL_COLORS.union(VIBRANT_COLORS)

STYLES = {'casual', 'sporty', 'elegant', 'formal', 'athletic', 'streetwear', 'minimalist', 'vintage', 'college', 'smart casual', 'cozy', 'knit', 'chic', 'classic'}

def get_stylist_category(item: Dict[str, Any]) -> str:
    name = item.get("product_name", item.get("name", "")).lower()
    desc = item.get("description", "").lower()
    cat = item.get("category", "").lower().replace(" ", "_")

    # Specific category patterns
    if "hoodie" in name or "hoodie" in desc or cat == "sweatshirts_hoodies":
        return "hoodie"
    if "bomber" in name or "bomber" in desc:
        return "bomber_jacket"
    if "denim jacket" in name or "denim jacket" in desc or "jean jacket" in name or "jean jacket" in desc or (cat == "denim" and "jacket" in name):
        return "denim_jacket"
    if "cardigan" in name or "cardigan" in desc or cat == "cardigans":
        return "cardigan"
    if "cargo" in name or "cargo" in desc:
        return "cargo_pants"
    if "jogger" in name or "jogger" in desc or "sweatpants" in name or "sweatpants" in desc:
        return "joggers"
    if "trouser" in name or "trouser" in desc:
        return "trousers"
    if "overshirt" in name or "overshirt" in desc or "shacket" in name or "shacket" in desc:
        return "overshirt"
    if "t-shirt" in name or "t-shirt" in desc or "t shirt" in name or "t shirt" in desc or "tee" in name or "tee" in desc or cat in ("tees_tanks", "graphic_tees"):
        return "tshirt"
    if "jeans" in name or "jeans" in desc or (cat == "denim" and ("jeans" in name or "jeans" in desc or "jean" in name or "pants" in name or "pants" in desc)):
        return "jeans"
    if "dress" in name or "dress" in desc or "gown" in name or "gown" in desc or cat == "dresses":
        return "dress"
    if cat == "shorts" or "shorts" in name or "shorts" in desc:
        return "shorts"
    if cat == "skirts" or "skirts" in name or "skirts" in desc:
        return "skirt"
    if cat in ("shirts_polos", "blouses_shirts") or "shirt" in name or "shirt" in desc or "blouse" in name or "blouse" in desc or "polo" in name or "polo" in desc:
        return "shirt"
    if cat == "sweaters" or "sweater" in name or "sweater" in desc or "pullover" in name or "pullover" in desc:
        return "sweater"
    if cat in ("jackets_coats", "jackets_vests") or "jacket" in name or "jacket" in desc or "coat" in name or "coat" in desc or "vest" in name or "vest" in desc or "blazer" in name or "blazer" in desc:
        return "jacket"
    if cat in ("rompers_jumpsuits", "suiting") or "romper" in name or "romper" in desc or "jumpsuit" in name or "jumpsuit" in desc or "suit" in name or "suit" in desc:
        return "one_piece"
    if cat == "pants" or "pants" in name or "pants" in desc or cat == "leggings" or "leggings" in name or "leggings" in desc:
        return "trousers"
        
    return "tshirt"  # Fallback default

def get_stylist_category_group(stylist_cat: str) -> str:
    if stylist_cat in ("hoodie", "tshirt", "shirt", "sweater"):
        return "top"
    elif stylist_cat in ("jeans", "cargo_pants", "joggers", "trousers", "shorts", "skirt"):
        return "bottom"
    elif stylist_cat in ("cardigan", "bomber_jacket", "denim_jacket", "jacket", "overshirt"):
        return "layer"
    elif stylist_cat in ("dress", "one_piece"):
        return "one_piece"
    return "top"

def extract_color(item: Dict[str, Any]) -> str:
    name = item.get("product_name", item.get("name", "")).lower()
    desc = item.get("description", "").lower()
    for word in name.split():
        word_cleaned = word.strip(".,;:()[]{}")
        if word_cleaned in ALL_COLORS:
            return word_cleaned
    for word in desc.split():
        word_cleaned = word.strip(".,;:()[]{}")
        if word_cleaned in ALL_COLORS:
            return word_cleaned
    return "neutral"

def extract_styles(item: Dict[str, Any]) -> set:
    name = item.get("product_name", item.get("name", "")).lower()
    desc = item.get("description", "").lower()
    tags = set()
    for style in STYLES:
        if style in name or style in desc:
            tags.add(style)
    return tags

OUTFIT_TEMPLATES = {
    "hoodie": [
        ["jeans", "bomber_jacket"],
        ["cargo_pants", "denim_jacket"],
        ["joggers", "bomber_jacket"]
    ],
    "tshirt": [
        ["jeans", "overshirt"],
        ["cargo_pants", "denim_jacket"]
    ],
    "denim_jacket": [
        ["tshirt", "jeans"],
        ["tshirt", "cargo_pants"]
    ],
    "dress": [
        ["cardigan"],
        ["jacket"]
    ],
    "sweater": [
        ["jeans", "trousers"]
    ],
    "shirt": [
        ["jeans", "jacket"],
        ["trousers", "jacket"],
        ["skirt", "cardigan"]
    ],
    "overshirt": [
        ["tshirt", "jeans"],
        ["tshirt", "cargo_pants"]
    ],
    "cardigan": [
        ["tshirt", "jeans"],
        ["shirt", "trousers"],
        ["dress"]
    ],
    "bomber_jacket": [
        ["tshirt", "jeans"],
        ["hoodie", "joggers"],
        ["tshirt", "cargo_pants"]
    ],
    "jacket": [
        ["tshirt", "jeans"],
        ["shirt", "trousers"],
        ["dress"]
    ],
    "jeans": [
        ["tshirt", "denim_jacket"],
        ["shirt", "bomber_jacket"],
        ["hoodie", "jacket"]
    ],
    "cargo_pants": [
        ["tshirt", "denim_jacket"],
        ["hoodie", "bomber_jacket"]
    ],
    "joggers": [
        ["tshirt", "bomber_jacket"],
        ["hoodie", "jacket"]
    ],
    "trousers": [
        ["shirt", "jacket"],
        ["sweater", "jacket"],
        ["tshirt", "cardigan"]
    ],
    "shorts": [
        ["tshirt", "cardigan"],
        ["shirt", "jacket"]
    ],
    "skirt": [
        ["tshirt", "cardigan"],
        ["shirt", "jacket"]
    ],
    "one_piece": [
        ["jacket"],
        ["cardigan"]
    ]
}

def score_candidate(
    candidate: Dict[str, Any],
    target: Dict[str, Any],
    target_category: str,
    target_color: str,
    target_styles: set,
    similarity_map: Dict[str, float],
    viewed_categories: set,
    viewed_colors: set,
    viewed_styles: set,
    viewed_ids: set
) -> float:
    candidate_id = candidate["product_id"]
    if candidate_id == target["product_id"]:
        return -999.0
    if candidate_id in viewed_ids:
        return -999.0
    if get_stylist_category(candidate) == target_category:
        return -999.0
        
    clip_similarity = similarity_map.get(candidate_id, 0.5)
    
    # Clip similarity is in [0, 1]. Map it to a base visual score (max weight 0.5)
    if clip_similarity > 0.95:
        clip_score = 0.5 * 0.95
    else:
        clip_score = 0.5 * clip_similarity
        
    # Color Harmony
    cand_color = extract_color(candidate)
    color_bonus = 0.0
    if target_color in NEUTRAL_COLORS or cand_color in NEUTRAL_COLORS:
        color_bonus = 0.15
    else:
        if target_color == cand_color:
            color_bonus = -0.20
        else:
            color_bonus = 0.05
            
    # Style Compatibility
    cand_styles = extract_styles(candidate)
    style_bonus = 0.0
    shared_styles = target_styles.intersection(cand_styles)
    if shared_styles:
        style_bonus = 0.15
        
    # Personalization (User History)
    pers_bonus = 0.0
    cand_category = get_stylist_category(candidate)
    if cand_category in viewed_categories:
        pers_bonus += 0.05
    if cand_color in viewed_colors:
        pers_bonus += 0.05
    if cand_styles.intersection(viewed_styles):
        pers_bonus += 0.05
        
    pers_bonus = min(0.25, pers_bonus)
    
    return clip_score + color_bonus + style_bonus + pers_bonus

class OutfitService:
    def __init__(self, image_search_service: ImageSearchService = None):
        if image_search_service is None:
            try:
                from backend.routes.image_search import get_search_service
                self.image_search_service = get_search_service()
            except Exception:
                self.image_search_service = ImageSearchService()
        else:
            self.image_search_service = image_search_service

    async def generate_outfit(
        self, 
        product_id: str, 
        recently_viewed_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a personalized styled outfit recommendation for a given product_id.
        Workflow:
        1. Look up target product details.
        2. Query FAISS index for all items visual similarity to get baseline visual compatibility scoring.
        3. Classify target product category and fetch complementary outfit templates.
        4. Personalize with browsing history.
        5. For each allowed template, find the best scoring candidate per slot.
        6. Select the outfit template that yields the highest cumulative styling score.
        7. Pass selected items to Gemini (LLM) to write stylist explanation.
        8. Return complete schema.
        """
        if self.image_search_service.index is None or self.image_search_service.metadata is None:
            self.image_search_service.load_index_and_metadata()

        # 1. Retrieve the selected target product
        target_product = None
        target_idx = -1
        for idx, p in enumerate(self.image_search_service.metadata):
            if p.get("product_id") == product_id:
                target_product = p
                target_idx = idx
                break

        if not target_product:
            raise ValueError(f"Product with ID {product_id} not found in metadata.")

        # Determine target details
        target_cat = get_stylist_category(target_product)
        target_color = extract_color(target_product)
        target_styles = extract_styles(target_product)

        # Get outfit rules/templates for target category
        Templates = OUTFIT_TEMPLATES.get(target_cat)
        if not Templates:
            # Fallback based on group
            fallback_group = get_stylist_category_group(target_cat)
            if fallback_group == "top":
                Templates = OUTFIT_TEMPLATES["tshirt"]
            elif fallback_group == "bottom":
                Templates = OUTFIT_TEMPLATES["trousers"]
            elif fallback_group == "layer":
                Templates = OUTFIT_TEMPLATES["jacket"]
            else:
                Templates = OUTFIT_TEMPLATES["one_piece"]

        # 2. Get similarity scores for all items using FAISS index of target_product
        similarity_map = {}
        try:
            query_vector = self.image_search_service.index.reconstruct(target_idx)
            total_products = len(self.image_search_service.metadata)
            distances, indices = execute_faiss_search(self.image_search_service.index, query_vector, top_k=total_products)
            for score, idx in zip(distances, indices):
                if idx == -1 or idx >= total_products:
                    continue
                pid = self.image_search_service.metadata[idx]["product_id"]
                similarity_map[pid] = float(max(0.0, min(1.0, score)))
        except Exception as e:
            logger.error(f"Error querying FAISS for visual similarity: {e}")

        # 3. Analyze recently viewed for style personalization hints
        recently_viewed_products = []
        viewed_categories = set()
        viewed_colors = set()
        viewed_styles = set()
        personalization_hint = ""
        
        viewed_ids = set()
        if recently_viewed_ids:
            viewed_ids = set(recently_viewed_ids[:8])
            for p in self.image_search_service.metadata:
                if p.get("product_id") in viewed_ids and p.get("product_id") != product_id:
                    recently_viewed_products.append(p)
                    
            for p in recently_viewed_products:
                viewed_categories.add(get_stylist_category(p))
                viewed_colors.add(extract_color(p))
                viewed_styles.update(extract_styles(p))
                
            if recently_viewed_products:
                categories_viewed = [p["category"] for p in recently_viewed_products]
                cats_str = ", ".join(set(categories_viewed))
                personalization_hint = (
                    f"The user has recently viewed items in categories: [{cats_str}]. "
                    f"If they frequently view comfortable/informal clothing, steer towards Casual, College, or Streetwear. "
                    f"If they view jackets/coats or tailored suiting, prefer Smart Casual or Minimalist styles."
                )

        # 4. Perform deterministic selection for each slot using the scoring system
        best_outfit_score = -9999.0
        best_outfit_products = []
        best_template = None

        for template in Templates:
            template_products = []
            template_score = 0.0
            used_ids = {product_id}
            selected_categories = {target_cat}
            
            valid_template = True
            for slot_category in template:
                # Enforce category diversity: slot category must not clash with target or existing slots
                if slot_category == target_cat or slot_category in selected_categories:
                    valid_template = False
                    break

                best_slot_item = None
                best_slot_score = -9999.0
                
                # Retrieve candidates of the exact stylist category from catalog
                for item in self.image_search_service.metadata:
                    if item["product_id"] in used_ids or item["product_id"] in viewed_ids:
                        continue
                        
                    item_stylist_cat = get_stylist_category(item)
                    if item_stylist_cat != slot_category:
                        continue
                    
                    # Exclude products matching target stylist category
                    if item_stylist_cat == target_cat:
                        continue

                    # Exclude products with a category already in the outfit
                    if item_stylist_cat in selected_categories:
                        continue
                        
                    score = score_candidate(
                        candidate=item,
                        target=target_product,
                        target_category=target_cat,
                        target_color=target_color,
                        target_styles=target_styles,
                        similarity_map=similarity_map,
                        viewed_categories=viewed_categories,
                        viewed_colors=viewed_colors,
                        viewed_styles=viewed_styles,
                        viewed_ids=used_ids
                    )
                    
                    if score > best_slot_score:
                        best_slot_score = score
                        best_slot_item = item
                
                if best_slot_item:
                    template_products.append(best_slot_item)
                    used_ids.add(best_slot_item["product_id"])
                    selected_categories.add(slot_category)
                    template_score += best_slot_score
                else:
                    valid_template = False
                    break
                    
            if valid_template and template_score > best_outfit_score:
                best_outfit_score = template_score
                best_outfit_products = template_products
                best_template = template

        recommended_products = best_outfit_products

        # Absolute fallback if no template generated any products
        if not recommended_products:
            logger.warning("No template was fully satisfied. Reverting to group fallback.")
            
            # Sort all metadata items by similarity score
            sorted_by_similarity = []
            for item in self.image_search_service.metadata:
                if item["product_id"] == product_id or item["product_id"] in viewed_ids:
                    continue
                sim = similarity_map.get(item["product_id"], 0.0)
                sorted_by_similarity.append((sim, item))
            sorted_by_similarity.sort(key=lambda x: x[0], reverse=True)
            
            recommended_products = []
            selected_categories = {target_cat}
            
            for sim, item in sorted_by_similarity:
                if len(recommended_products) >= 2:
                    break
                cand_cat = get_stylist_category(item)
                # Hard filter: exclude if it is the target category or already selected
                if cand_cat == target_cat or cand_cat in selected_categories:
                    continue
                
                recommended_products.append(item)
                selected_categories.add(cand_cat)

        if not recommended_products:
            raise ValueError("No valid products were matched from the recommendation list.")

        # 5. Call LLM to generate the explanation
        system_instruction = (
            "You are the NovaLens AI Fashion Stylist, a state-of-the-art AI fashion consultant. "
            "The stylist algorithm has selected a perfect, coherent complementary outfit for a target product. "
            "Your job is to write a concise stylist explanation (maximum 2-3 sentences) explaining why this outfit works together, focusing on style compatibility, color harmony, and overall outfit coherence. "
            "You should also assign a suitable outfit style name and a general style category (selected from: Casual, College, Streetwear, Smart Casual, Winter Wear, Minimalist, Everyday Wear). "
            "\n\n"
            "CRITICAL RULES:\n"
            "1. ONLY EXPLAIN: Do not suggest or select any other products. You must only explain the combination of the target product and the recommended products provided to you.\n"
            "2. RESPONSE FORMAT: You must output ONLY a valid JSON object. Do not wrap it in markdown block styles or include any other introductory/conversational text. "
            "All string values in the JSON (especially the 'explanation') MUST be single-line strings. Do not include raw newlines or line breaks inside string values, as this will break JSON parsing.\n"
            "The JSON structure must match exactly:\n"
            "{\n"
            "  \"outfit_name\": \"Brief name of the outfit style (e.g. Streetwear Autumn Vibe)\",\n"
            "  \"style\": \"The selected style name from the supported list above (e.g. Streetwear)\",\n"
            "  \"explanation\": \"A styling explanation explaining why these items work together, color coordination, and occasion logic.\"\n"
            "}"
        )

        rec_details_list = []
        for idx, item in enumerate(recommended_products):
            desc = item.get("description", "No description available.")
            rec_details_list.append(
                f"Recommended Product {idx+1}:\n"
                f"Product ID: {item['product_id']}\n"
                f"Name: {item['name']}\n"
                f"Category: {item['category']}\n"
                f"Price: ₹{item['price']}\n"
                f"Description: {desc}\n"
            )
        rec_details_str = "\n".join(rec_details_list)

        prompt_messages = [
            {
                "role": "user",
                "content": (
                    f"Target Product to Style:\n"
                    f"Product ID: {target_product['product_id']}\n"
                    f"Name: {target_product['name']}\n"
                    f"Category: {target_product['category']}\n"
                    f"Price: ₹{target_product['price']}\n"
                    f"Description: {target_product.get('description', '')}\n\n"
                    f"Selected complementary items to explain:\n"
                    f"{rec_details_str}\n"
                    f"Personalization Hint: {personalization_hint}\n\n"
                    f"Please generate the outfit explanation now."
                )
            }
        ]

        llm_service = LLMService()
        raw_response = ""
        try:
            raw_response = await llm_service.generate_response(
                system_instruction=system_instruction,
                messages=prompt_messages,
                temperature=0.7
            )
            clean_res = raw_response.strip()
            if clean_res.startswith("```"):
                lines = clean_res.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                clean_res = "\n".join(lines).strip()
            
            clean_res = sanitize_json_string(clean_res)
            result_json = json.loads(clean_res)
            
            outfit_name = result_json.get("outfit_name", "Complete the Look")
            outfit_style = result_json.get("style", "Casual")
            explanation = result_json.get("explanation", "A perfectly coordinated outfit to match your style.")
            
            return {
                "outfit_name": outfit_name,
                "style": outfit_style,
                "explanation": explanation,
                "products": recommended_products
            }
            
        except Exception as e:
            logger.error(f"Failed to generate outfit explanation via LLM: {e}. Raw response was: {raw_response}")
            # Determine overall styling aesthetic from shared tags or fallback
            determined_style = "Everyday Wear"
            if target_styles:
                determined_style = list(target_styles)[0].title()
                if determined_style not in ("Casual", "College", "Streetwear", "Smart Casual", "Winter Wear", "Minimalist", "Everyday Wear"):
                    determined_style = "Everyday Wear"

            rec_names = " and ".join([p["name"] for p in recommended_products])
            explanation = (
                f"A stylish, coordinated {determined_style} look featuring your selected {target_product['name']} "
                f"effortlessly paired with {rec_names} to create a coherent color and style balance."
            )
            return {
                "outfit_name": f"Styled {determined_style} Outfit",
                "style": determined_style,
                "explanation": explanation,
                "products": recommended_products
            }
