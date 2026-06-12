import os
import random
import pandas as pd

def is_valid_image_header(path: str) -> bool:
    """
    Very fast check of the image file header (magic bytes) to avoid
    heavy I/O overhead of loading files into Pillow.
    """
    try:
        if os.path.getsize(path) == 0:
            return False
        with open(path, 'rb') as f:
            header = f.read(4)
            # JPEG: FF D8 FF
            if header[:3] == b'\xff\xd8\xff':
                return True
            # PNG: 89 50 4E 47
            if header == b'\x89PNG':
                return True
            # WEBP: RIFF....WEBP
            if header == b'RIFF':
                f.seek(8)
                webp = f.read(4)
                if webp == b'WEBP':
                    return True
        return False
    except Exception:
        return False

def prepare_dataset():
    # Path definitions
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    styles_path = os.path.join(base_dir, "data", "fashion", "styles.csv")
    images_dir = os.path.join(base_dir, "data", "fashion", "images")
    output_csv_path = os.path.join(base_dir, "data", "products.csv")
    
    print(f"Starting dataset preparation...", flush=True)
    print(f"Reading styles.csv from: {styles_path}", flush=True)
    
    if not os.path.exists(styles_path):
        print(f"Error: Styles CSV not found at {styles_path}", flush=True)
        return
        
    # Read CSV, skip lines with formatting errors
    try:
        df = pd.read_csv(styles_path, on_bad_lines='skip')
    except Exception as e:
        print(f"Error reading styles.csv: {e}", flush=True)
        return
        
    print(f"Total records loaded from styles.csv: {len(df)}", flush=True)
    
    prepared_products = []
    seen_ids = set()
    
    # Track statistics
    skipped_missing = 0
    skipped_corrupted = 0
    skipped_invalid_id = 0
    skipped_duplicate = 0
    skipped_missing_name = 0
    skipped_missing_category = 0
    
    for idx, row in df.iterrows():
        # Print progress every 5000 rows
        if idx > 0 and idx % 5000 == 0:
            print(f"Processed validation for {idx}/{len(df)} rows...", flush=True)
            
        # 1. Validate product ID
        try:
            raw_id = row.get('id')
            if pd.isna(raw_id):
                skipped_invalid_id += 1
                continue
            product_id = str(int(raw_id))
        except Exception:
            skipped_invalid_id += 1
            continue
            
        # 2. Check for duplicate product IDs
        if product_id in seen_ids:
            skipped_duplicate += 1
            continue
            
        # 3. Validate name (productDisplayName)
        name = row.get('productDisplayName')
        if pd.isna(name) or not str(name).strip():
            skipped_missing_name += 1
            continue
        name = str(name).strip()
        
        # 4. Validate category (articleType)
        category = row.get('articleType')
        if pd.isna(category) or not str(category).strip():
            skipped_missing_category += 1
            continue
        category = str(category).strip()
        
        # 5. Check image file existence and integrity
        image_filename = f"{product_id}.jpg"
        image_path = os.path.join(images_dir, image_filename)
        
        if not os.path.exists(image_path):
            skipped_missing += 1
            continue
            
        if not is_valid_image_header(image_path):
            skipped_corrupted += 1
            print(f"Warning: Invalid or corrupted image header for product ID '{product_id}' at {image_path}", flush=True)
            continue
            
        # 6. Build description (masterCategory + subCategory)
        master_cat = str(row.get('masterCategory', '')).strip()
        sub_cat = str(row.get('subCategory', '')).strip()
        description = f"{master_cat} - {sub_cat}"
        
        # 7. Generate realistic synthetic price (INR)
        random.seed(int(product_id))
        sub_cat_lower = sub_cat.lower()
        art_type_lower = category.lower()
        
        if 'tshirt' in art_type_lower or 't-shirt' in art_type_lower or 'tee' in art_type_lower:
            price = float(random.randint(499, 1499))
        elif any(x in sub_cat_lower or x in art_type_lower for x in ['shoe', 'sandal', 'flip flop', 'flats', 'footwear']):
            price = float(random.randint(1999, 6999))
        elif 'watch' in sub_cat_lower or 'watch' in art_type_lower:
            price = float(random.randint(999, 9999))
        elif 'bag' in sub_cat_lower or 'bag' in art_type_lower or 'backpack' in art_type_lower:
            price = float(random.randint(799, 4999))
        else:
            price = float(random.randint(299, 2999))
            
        # Save details
        prepared_products.append({
            "product_id": product_id,
            "name": name,
            "category": category,
            "description": description,
            "price": price,
            "image_path": f"fashion/images/{image_filename}"
        })
        seen_ids.add(product_id)
        
    print(f"Validation loop finished.", flush=True)
    print(f"Skipped invalid IDs: {skipped_invalid_id}", flush=True)
    print(f"Skipped duplicates: {skipped_duplicate}", flush=True)
    print(f"Skipped missing name: {skipped_missing_name}", flush=True)
    print(f"Skipped missing category: {skipped_missing_category}", flush=True)
    print(f"Skipped missing image file: {skipped_missing}", flush=True)
    print(f"Skipped corrupted image header: {skipped_corrupted}", flush=True)
    
    # Write to products.csv
    out_df = pd.DataFrame(prepared_products)
    out_df.to_csv(output_csv_path, index=False)
    print(f"Dataset preparation complete! Saved {len(out_df)} valid products to: {output_csv_path}", flush=True)

if __name__ == "__main__":
    prepare_dataset()
