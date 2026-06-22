import os
import sys
import json
import math
import hashlib
import logging
from typing import List, Dict, Any
import urllib.parse
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.llm_service import LLMService
from backend.services.retailer_connectors import (
    AmazonConnector,
    FlipkartConnector,
    MyntraConnector,
    AjioConnector,
    TataCliqConnector
)
from backend.utils.image_utils import is_valid_product_image

logger = logging.getLogger("novalens.shopping_intelligence")

class ShoppingIntelligenceService:
    def __init__(self):
        # Configurable Weights for Shopping Score
        self.w_rating = 0.40
        self.w_reviews = 0.30
        self.w_price = 0.20
        self.w_trust = 0.10

        # Retailer trust values
        self.retailer_trust = {
            "Amazon": 1.00,
            "Myntra": 0.95,
            "Ajio": 0.93,
            "Flipkart": 0.92,
            "Tata Cliq": 0.90
        }

        # Initialize connectors
        self.connectors = {
            "Amazon": AmazonConnector(),
            "Flipkart": FlipkartConnector(),
            "Myntra": MyntraConnector(),
            "Ajio": AjioConnector(),
            "Tata Cliq": TataCliqConnector()
        }

    def simplify_query(self, name: str, category: str) -> str:
        """
        Simplifies long catalog product names into clean, retailer-friendly search queries
        by removing hyper-specific descriptors and dataset noise.
        """
        import re
        
        # Lowercase
        query = name.lower()
        
        # Remove possessives
        query = query.replace("'s", "").replace("’s", "")
        
        # Remove punctuation / special characters
        query = re.sub(r"[^\w\s-]", " ", query)
        
        # Remove noisy visual description adjectives
        noise_words = {
            "soft-knit", "soft knit", "knitted", "printed", "striped", "casual", "premium", 
            "fashion", "slimming", "fit", "stretch", "soft", "comfortable", "classic", 
            "stylish", "vintage", "retro", "chic", "elegant", "fancy", "modern", "gorgeous", 
            "beautiful", "pretty", "handsome", "cute", "lovely", "perfect", "amazing", "best", 
            "quality", "value", "exclusive", "latest", "new", "original", "authentic", "brand", 
            "collection", "style", "wear", "apparel", "clothing", "item", "product", "detail", 
            "inclusive", "gst", "premium", "luxury", "solid", "patterned", "textured", "woven", 
            "embroidered", "embellished"
        }
        
        words = query.split()
        filtered_words = [w for w in words if w not in noise_words]
        
        # If filtered query is empty, fallback to category
        if not filtered_words:
            return category if category else "Fashion"
            
        simplified = " ".join(filtered_words)
        
        # Capitalize words
        simplified = " ".join(w.capitalize() for w in simplified.split())
        
        # If still too long, limit to max 4 words
        words = simplified.split()
        if len(words) > 4:
            simplified = " ".join(words[:4])
            
        return simplified

    def calculate_match_confidence(self, product: Dict[str, Any], offer: Dict[str, Any]) -> float:
        """
        Calculates match confidence based on title, category, color, and brand similarity.
        match_score = 0.50 * title_similarity + 0.20 * category_similarity + 0.15 * color_similarity + 0.15 * brand_similarity
        """
        import re
        p_name = (product.get("name") or product.get("product_name") or "").lower()
        o_name = offer.get("product_name", "").lower()
        
        # Clean punctuation from names to improve word token matching
        p_clean = re.sub(r"[^\w\s]", " ", p_name)
        o_clean = re.sub(r"[^\w\s]", " ", o_name)
        
        p_tokens = set(p_clean.split())
        o_tokens = set(o_clean.split())
        
        intersection = p_tokens.intersection(o_tokens)
        union = p_tokens.union(o_tokens)
        title_sim = len(intersection) / len(union) if union else 0.0
        
        # Category match
        p_cat = product.get("category", "").lower()
        o_cat = offer.get("category", "").lower()
        cat_sim = 1.0
        if p_cat and o_cat:
            generic_categories = {"fashion", "clothing", "apparel", "style", "wear"}
            is_generic = o_cat in generic_categories or p_cat in generic_categories
            
            cat_sim = 1.0 if (p_cat in o_cat or o_cat in p_cat or is_generic) else 0.0
            if cat_sim == 0.0:
                # Group-based matching (e.g. pants/jeans/denim are Bottoms, sweaters/shirts are Tops, rompers/jumpsuits are Dresses)
                bottoms_synonyms = {"bottoms", "pants", "jeans", "shorts", "leggings", "skirts", "denim", "jackets_vests", "jackets_coats", "suiting"}
                tops_synonyms = {"tops", "shirts", "polos", "sweaters", "hoodies", "tees", "tanks", "blouses", "cardigans", "graphic", "sweatshirts_hoodies", "graphic_tees", "tees_tanks", "blouses_shirts"}
                dresses_synonyms = {"dresses", "rompers_jumpsuits", "romper", "jumpsuit", "dress"}
                
                p_words = set(re.findall(r'\w+', p_cat))
                o_words = set(re.findall(r'\w+', o_cat))
                
                both_bottoms = (p_words.intersection(bottoms_synonyms) and o_words.intersection(bottoms_synonyms))
                both_tops = (p_words.intersection(tops_synonyms) and o_words.intersection(tops_synonyms))
                both_dresses = (p_words.intersection(dresses_synonyms) and o_words.intersection(dresses_synonyms))
                
                if both_bottoms or both_tops or both_dresses:
                    cat_sim = 0.8
                else:
                    return 0.0
        
        # Color match
        colors = ["rust", "black", "blue", "white", "red", "green", "yellow", "grey", "gray", "brown", "pink"]
        p_color = next((c for c in colors if c in p_name), None)
        o_color = next((c for c in colors if c in o_name), None)
        
        color_sim = 1.0
        if p_color and o_color:
            color_sim = 1.0 if p_color == o_color else 0.0
            
        # Brand similarity
        p_brand = product.get("brand", "").lower().strip()
        o_brand = offer.get("brand", "").lower().strip()
        brand_sim = 1.0
        if p_brand and o_brand:
            brand_sim = 1.0 if (p_brand in o_brand or o_brand in p_brand) else 0.0
        elif o_brand:
            brand_sim = 1.0 if o_brand in p_name else 0.0
            
        if cat_sim == 0.0:
            return 0.0
            
        return 0.50 * title_sim + 0.20 * cat_sim + 0.15 * color_sim + 0.15 * brand_sim

    async def retrieve_retailer_offers(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Uses Connector Architecture to fetch and normalize retailer product offers.
        Prioritizes preferred ones with detailed diagnostics.
        """
        p_name = product.get("name", "Fashion Item")
        p_cat = product.get("category", "")
        simplified_query = self.simplify_query(p_name, p_cat)

        log_msg_query = f"Query:\n{simplified_query}"
        logger.info(log_msg_query)
        print(log_msg_query)

        tasks = []
        retailers = []
        for name, connector in self.connectors.items():
            tasks.append(connector.search_products(simplified_query, product))
            retailers.append(name)

        results = await asyncio.gather(*tasks)

        all_offers = []
        for name, connector_results in zip(retailers, results):
            logger.info(f"{name}Connector:")
            logger.info(f"  Raw Products = {len(connector_results)}")
            logger.info(f"  After Normalization = {len(connector_results)}")
            print(f"{name}Connector:")
            print(f"  Raw Products = {len(connector_results)}")
            print(f"  After Normalization = {len(connector_results)}")
            for o in connector_results:
                all_offers.append(o)

        # Image URL Normalization & Fallback check
        catalog_image = product.get("image_path", "")
        for o in all_offers:
            img = o.get("image_url") or o.get("product_image")
            
            # Check validation using our custom utility
            is_valid = is_valid_product_image(img)
            
            if not is_valid:
                # Priority 2: Alternative Retailer Image
                alt_img = o.get("alternative_image_url")
                if alt_img and is_valid_product_image(alt_img):
                    img = alt_img
                else:
                    # Priority 3: Catalog image fallback
                    img = catalog_image
            
            o["image_url"] = img
            o["product_image"] = img

        # Apply Product Matching
        matched_offers = []
        connector_matched_counts = {name: 0 for name in retailers}
        
        logger.info("Applying Product Matching Confidence Filters:")
        print("Applying Product Matching Confidence Filters:")
        for o in all_offers:
            confidence = self.calculate_match_confidence(product, o)
            is_img_valid = is_valid_product_image(o.get("image_url"))
            
            # Debugging log requirements format:
            # Retailer
            # Product Name
            # Image URL
            # Image Valid status (VALID/INVALID)
            # Match Score
            print(o["retailer"])
            print(o["product_name"])
            print(o["image_url"])
            print("VALID" if is_img_valid else "INVALID")
            print(f"{confidence:.2f}")
            
            log_match_cand = f"  - Product: '{o['product_name']}' from {o['retailer']} | Confidence score = {confidence:.4f} | Matching threshold = 0.2"
            logger.info(log_match_cand)
            print(log_match_cand)
            
            if confidence >= 0.2:
                matched_offers.append(o)
                connector_matched_counts[o['retailer']] += 1

        for name in retailers:
            log_match_count = f"  {name}Connector After Matching = {connector_matched_counts[name]}"
            logger.info(log_match_count)
            print(log_match_count)

        # Prioritize preferred retailers
        preferred_set = {"Amazon", "Myntra", "Ajio", "Flipkart", "Tata Cliq"}
        matched_offers.sort(key=lambda x: 0 if x["retailer"] in preferred_set else 1)

        log_final_count = f"Final Products Sent = {len(matched_offers)}"
        logger.info(log_final_count)
        print(log_final_count)

        # Diagnostics: If final count becomes zero, log exactly which stage removed all products
        if len(matched_offers) == 0:
            if len(all_offers) == 0:
                logger.error("DIAGNOSTIC FAILURE: All connectors returned 0 raw products. Query returned nothing.")
                print("DIAGNOSTIC FAILURE: All connectors returned 0 raw products. Query returned nothing.")
            else:
                diag_fail_msg = f"DIAGNOSTIC FAILURE: Direct scraping / Fallback returned {len(all_offers)} total raw products, but confidence matching filtered them all out to 0 (threshold = 0.2)."
                logger.error(diag_fail_msg)
                print(diag_fail_msg)

        return matched_offers

    def score_offers(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Computes the Shopping Intelligence Score for each retailer offer.
        shopping_score = 0.40 * rating_score + 0.30 * review_confidence + 0.20 * price_score + 0.10 * retailer_trust
        """
        if not offers:
            return []

        prices = [o["price"] for o in offers]
        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0

        scored_offers = []
        for o in offers:
            rating_score = o["rating"] / 5.0
            review_confidence = 1.0 - math.exp(-o["review_count"] / 300.0)

            if max_price > min_price:
                price_score = (max_price - o["price"]) / (max_price - min_price)
            else:
                price_score = 1.0

            retailer_name = o["retailer"]
            trust = self.retailer_trust.get(retailer_name, 0.80)

            composite = (
                self.w_rating * rating_score +
                self.w_reviews * review_confidence +
                self.w_price * price_score +
                self.w_trust * trust
            )

            o["shopping_score"] = round(composite, 2)
            scored_offers.append(o)

        ratings = [o["rating"] for o in scored_offers]
        max_rating = max(ratings) if ratings else 0.0
        scores = [o["shopping_score"] for o in scored_offers]
        max_score = max(scores) if scores else 0.0
        reviews = [o["review_count"] for o in scored_offers]
        max_reviews = max(reviews) if reviews else 0

        for o in scored_offers:
            print(f"{o['product_name']} score={o['shopping_score']}")

        scored_offers.sort(key=lambda x: x["shopping_score"], reverse=True)

        if scored_offers:
            print(f"Best Value Product: {scored_offers[0]['product_name']}")
            
            best_price_offer = min(scored_offers, key=lambda p: p["price"])
            best_quality_offer = max(scored_offers, key=lambda p: (p["rating"], p["review_count"]))
            best_value_offer = scored_offers[0]
            max_reviews = max(o["review_count"] for o in scored_offers)

            for idx, o in enumerate(scored_offers):
                o["is_best_value"] = (o == best_value_offer)
                o["is_best_price"] = (o == best_price_offer)
                o["is_best_quality"] = (o == best_quality_offer)
                o["is_most_popular"] = (o["review_count"] == max_reviews)

        return scored_offers

    async def generate_shopping_analysis(
        self,
        product: Dict[str, Any],
        scored_offers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Invokes LLM to perform the Shopping Analysis summary based on actual retrieved data.
        Handles empty comparative states by showing catalog data only.
        """
        # 8. Empty State check
        if not scored_offers:
            cat_price = product.get("price", 0.0)
            return {
                "best_price_explanation": f"The original catalog option from our store is the only available option at ₹{cat_price}.",
                "best_quality_explanation": "No customer reviews or quality ratings are available from other retailers.",
                "best_overall_explanation": f"The original catalog product at ₹{cat_price} is selected as the default choice.",
                "buying_summary": "No comparable retailer products were found. Showing catalog information only."
            }

        # Calculate exact best price, quality, and value in python
        # 2. Best Price logic: min by price
        best_price = min(scored_offers, key=lambda p: p["price"])
        # 3. Best Quality logic: max by rating, then review count
        best_quality = max(scored_offers, key=lambda p: (p["rating"], p["review_count"]))
        # 4. Best Overall Value logic: first sorted item (highest shopping score)
        best_value = scored_offers[0]

        system_instruction = (
            "You are the NovaLens AI Shopping Analyst, a specialist in price comparison, value analysis, and buying recommendations. "
            "Your job is to write a concise buying analysis summary and explain the recommended choices (Best Price, Best Quality, and Best Overall Value) based ONLY on the provided retailer comparison data. "
            "Do not invent or hallucinate any other retailers, prices, or options. "
            "Do not mention the original catalog product name or its catalog price. Base your decisions strictly on the compared retailer offers. "
            "\n\n"
            "CRITICAL: For each explanation (Best Price, Best Quality, Best Overall Value), you MUST explicitly mention: "
            "1. The Retailer Name (e.g. Myntra, Ajio, Amazon, Flipkart, Tata Cliq)\n"
            "2. The Price (e.g. ₹2299)\n"
            "3. The Rating (e.g. 4.6 stars)\n"
            "4. The Review Count (e.g. 3500 reviews)\n"
            "Do not use generic statements like 'Original catalog option is the only available choice'. "
            "\n\n"
            "RESPONSE FORMAT: You must output ONLY a valid JSON object. Do not wrap it in markdown block styles or include any other text. "
            "All string values in the JSON MUST be single-line strings. Do not include raw newlines inside string values. "
            "The JSON structure must match exactly:\n"
            "{\n"
            "  \"best_price_explanation\": \"Explanation of why this option is the best price and which retailer offers it.\",\n"
            "  \"best_quality_explanation\": \"Explanation of why this option is the best quality based on ratings/reviews, and which retailer offers it.\",\n"
            "  \"best_overall_explanation\": \"Explanation of why this option is the best overall value and which retailer offers it.\",\n"
            "  \"buying_summary\": \"A concise 2-sentence summary advising the user on which choice is best depending on their goals (e.g. if your priority is lowest cost, choose [Retailer Name]; if your priority is highest quality, choose [Retailer Name]; for the best overall value, [Retailer Name] is the recommended purchase).\"\n"
            "}"
        )

        offers_str = ""
        for idx, o in enumerate(scored_offers):
            offers_str += (
                f"Option {idx+1}:\n"
                f"Retailer: {o['retailer']}\n"
                f"Brand: {o['brand']}\n"
                f"Product: {o['product_name']}\n"
                f"Price: ₹{o['price']}\n"
                f"Rating: {o['rating']} stars\n"
                f"Reviews: {o['review_count']} reviews\n"
                f"Shopping Intelligence Score: {int(o['shopping_score']*100)}/100\n\n"
            )

        prompt_messages = [
            {
                "role": "user",
                "content": (
                    f"Retailer Offers Comparison Data:\n"
                    f"{offers_str}\n"
                    f"Selected Best Offers:\n"
                    f"- Best Price Offer is from {best_price['retailer']} at ₹{best_price['price']} with {best_price['rating']} stars and {best_price['review_count']} reviews.\n"
                    f"- Best Quality Offer is from {best_quality['retailer']} at ₹{best_quality['price']} with {best_quality['rating']} stars and {best_quality['review_count']} reviews.\n"
                    f"- Best Overall Value is from {best_value['retailer']} at ₹{best_value['price']} with {best_value['rating']} stars and {best_value['review_count']} reviews.\n\n"
                    f"Please generate the AI Shopping Intelligence buying recommendation JSON now. Remember that every explanation MUST explicitly mention the retailer name, price, rating, and review count for that option."
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

            result_json = json.loads(clean_res)
            return {
                "best_price_explanation": result_json.get("best_price_explanation", f"{best_price['retailer']} offers the lowest price of ₹{best_price['price']} ({best_price['rating']} stars, {best_price['review_count']} reviews)."),
                "best_quality_explanation": result_json.get("best_quality_explanation", f"{best_quality['retailer']} provides the highest quality with a {best_quality['rating']}-star rating and {best_quality['review_count']} reviews at ₹{best_quality['price']}."),
                "best_overall_explanation": result_json.get("best_overall_explanation", f"{best_value['retailer']} provides the best overall value at ₹{best_value['price']} ({best_value['rating']} stars, {best_value['review_count']} reviews)."),
                "buying_summary": result_json.get("buying_summary", f"If lowest cost is key, choose {best_price['retailer']}. If quality matters most, choose {best_quality['retailer']}. For overall value, choose {best_value['retailer']}.")
            }
        except Exception as e:
            logger.error(f"Failed to generate shopping analysis: {e}. Raw response: {raw_response}")
            
            p_ret, p_price, p_rat, p_rev = best_price['retailer'], best_price['price'], best_price['rating'], best_price['review_count']
            q_ret, q_price, q_rat, q_rev = best_quality['retailer'], best_quality['price'], best_quality['rating'], best_quality['review_count']
            v_ret, v_price, v_rat, v_rev = best_value['retailer'], best_value['price'], best_value['rating'], best_value['review_count']
            
            return {
                "best_price_explanation": f"{p_ret} offers the best price of ₹{p_price} ({p_rat} stars, {p_rev} reviews), making it the cheapest budget pick.",
                "best_quality_explanation": f"{q_ret} provides the highest rated option of {q_rat} stars ({q_rev} reviews) at ₹{q_price} for quality confidence.",
                "best_overall_explanation": f"{v_ret} is the recommended smart pick at ₹{v_price} ({v_rat} stars, {v_rev} reviews) based on our value score.",
                "buying_summary": f"If your priority is lowest cost, choose {p_ret} (₹{p_price}). For the best quality, choose {q_ret} ({q_rat} stars). For overall balance, we recommend {v_ret}."
            }
