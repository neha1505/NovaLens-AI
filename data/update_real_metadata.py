import os
import sys
import torch
import clip
import pandas as pd
from PIL import Image
import time

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ml.clip.clip_loader import CLIPLoader

def update_metadata_with_clip():
    print("=== Generating Accurate Visual Metadata using Fast Batch CLIP ===", flush=True)
    
    loader = CLIPLoader()
    model, preprocess = loader.get_model_and_preprocess()
    device = loader.get_device()

    categories = [
        "denim jacket", "leather jacket", "t-shirt", "button-down shirt", 
        "jeans", "shorts", "dress", "skirt", "sweater", "hoodie", 
        "coat", "blazer", "pants", "suit", "cardigan", "vest", "blouse"
    ]
    colors = [
        "blue", "black", "white", "red", "grey", "green", "brown", 
        "pink", "yellow", "navy blue", "beige", "maroon", "khaki", "olive green"
    ]

    cat_prompts = [f"a photo of a {c}" for c in categories]
    color_prompts = [f"a photo of {c} clothing" for c in colors]

    with torch.no_grad():
        cat_tokens = clip.tokenize(cat_prompts).to(device)
        cat_text_features = model.encode_text(cat_tokens)
        cat_text_features /= cat_text_features.norm(dim=-1, keepdim=True)

        color_tokens = clip.tokenize(color_prompts).to(device)
        color_text_features = model.encode_text(color_tokens)
        color_text_features /= color_text_features.norm(dim=-1, keepdim=True)

    csv_path = os.path.join(base_dir, "data", "processed", "products.csv")
    df = pd.read_csv(csv_path)
    total = len(df)
    
    category_map = {
        "denim jacket": "Denim",
        "jeans": "Denim",
        "leather jacket": "Jackets_Coats",
        "coat": "Jackets_Coats",
        "blazer": "Suiting",
        "suit": "Suiting",
        "t-shirt": "Tees_Tanks",
        "button-down shirt": "Shirts_Polos",
        "blouse": "Blouses_Shirts",
        "shorts": "Shorts",
        "dress": "Dresses",
        "skirt": "Skirts",
        "sweater": "Sweaters",
        "cardigan": "Cardigans",
        "hoodie": "Sweatshirts_Hoodies",
        "pants": "Pants",
        "vest": "Jackets_Vests"
    }

    batch_size = 128
    updated_rows = []
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batch_tensors = []
        batch_indices = []

        for b_idx, (_, row) in enumerate(batch_df.iterrows()):
            img_rel = row['primary_image']
            img_abs = os.path.join(base_dir, "data", "DeepFashion", img_rel)
            if not os.path.exists(img_abs):
                img_abs = os.path.join(base_dir, "data", img_rel)

            if os.path.exists(img_abs):
                try:
                    img = Image.open(img_abs).convert("RGB")
                    tensor = preprocess(img)
                    batch_tensors.append(tensor)
                    batch_indices.append(b_idx)
                except Exception:
                    pass

        # Perform fast batch inference
        preds_for_batch = {}
        if batch_tensors:
            with torch.no_grad():
                stacked = torch.stack(batch_tensors).to(device)
                img_features = model.encode_image(stacked)
                img_features /= img_features.norm(dim=-1, keepdim=True)

                cat_probs = (100.0 * img_features @ cat_text_features.T).softmax(dim=-1)
                color_probs = (100.0 * img_features @ color_text_features.T).softmax(dim=-1)

                top_cat_indices = cat_probs.argmax(dim=-1).cpu().tolist()
                top_color_indices = color_probs.argmax(dim=-1).cpu().tolist()

                for local_idx, c_idx, col_idx in zip(batch_indices, top_cat_indices, top_color_indices):
                    preds_for_batch[local_idx] = (categories[c_idx], colors[col_idx])

        # Construct updated metadata
        for b_idx, (_, row) in enumerate(batch_df.iterrows()):
            pred_cat, pred_color = preds_for_batch.get(b_idx, ("apparel", "classic"))
            gender_prefix = "Women's" if "WOMEN" in str(row['product_id']) else "Men's"
            
            real_title = f"{gender_prefix} {pred_color.title()} {pred_cat.title()}"
            real_category = category_map.get(pred_cat, row.get('category', 'Fashion'))
            real_desc = f"A stylish {real_title.lower()} featuring a comfortable fit, crafted from high quality fabric. Ideal for everyday wear."

            row_dict = row.to_dict()
            row_dict['product_name'] = real_title
            row_dict['category'] = real_category
            row_dict['description'] = real_desc
            updated_rows.append(row_dict)

        elapsed = time.time() - start_time
        print(f"Processed {min(i + batch_size, total)}/{total} items ({((min(i + batch_size, total))/total)*100:.1f}%) in {elapsed:.1f}s", flush=True)

    new_df = pd.DataFrame(updated_rows)
    new_df.to_csv(csv_path, index=False)
    print(f"=== Successfully updated products.csv with REAL visual content titles ===", flush=True)

if __name__ == "__main__":
    update_metadata_with_clip()
