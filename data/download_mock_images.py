import os
import csv
import urllib.request
from typing import List, Dict, Any

def download_subset(limit: int = 150):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "processed", "products.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: products.csv not found at {csv_path}")
        return
        
    print(f"Reading product metadata from {csv_path}...")
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
            
    print(f"Total products in catalog: {len(products)}")
    
    # Extract unique image paths and group by category
    unique_images = {}
    for p in products:
        path = p.get("primary_image", p.get("image_path", ""))
        category = p.get("category", "")
        if path and path not in unique_images:
            unique_images[path] = category
            
    print(f"Found {len(unique_images)} unique image paths.")
    
    # Download a subset of images
    download_list = list(unique_images.items())[:limit]
    print(f"Downloading a mock subset of {len(download_list)} fashion images to replicate the dataset...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    success_count = 0
    for idx, (img_path, category) in enumerate(download_list, 1):
        dest_path = os.path.join(base_dir, "data", img_path)
        dest_dir = os.path.dirname(dest_path)
        
        # Create directories if they do not exist
        os.makedirs(dest_dir, exist_ok=True)
        
        # Clean category for tags
        cat_tag = category.lower().replace('_', ',')
        url = f"https://loremflickr.com/400/500/fashion,apparel,{cat_tag}?lock={idx}"
        
        print(f"[{idx}/{limit}] Downloading placeholder for category '{category}' to: {dest_path}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(dest_path, 'wb') as out_file:
                    out_file.write(response.read())
            success_count += 1
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            
    print(f"\nCompleted! Successfully downloaded {success_count}/{limit} images to {os.path.join(base_dir, 'data', 'DeepFashion')}.")

if __name__ == "__main__":
    download_subset()
