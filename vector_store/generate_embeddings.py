import os
import sys
import pandas as pd
import numpy as np
import torch
import time
from PIL import Image
import argparse

# Add base directory to python path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ml.clip.clip_loader import CLIPLoader

def check_image_header(path: str) -> bool:
    try:
        if os.path.getsize(path) == 0:
            return False
        with open(path, 'rb') as f:
            header = f.read(4)
            if header[:3] == b'\xff\xd8\xff':
                return True
            if header == b'\x89PNG':
                return True
            if header == b'RIFF':
                f.seek(8)
                webp = f.read(4)
                if webp == b'WEBP':
                    return True
        return False
    except Exception:
        return False

def generate_embeddings():
    parser = argparse.ArgumentParser(description="Generate CLIP embeddings for DeepFashion product images.")
    parser.add_argument('--limit', type=int, default=-1, help='Limit the number of products to process (default: -1 for all).')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for CLIP embedding generation.')
    args = parser.parse_args()

    csv_path = os.path.join(base_dir, "data", "processed", "products.csv")
    data_dir = os.path.join(base_dir, "data")
    output_embeddings_path = os.path.join(base_dir, "data", "processed", "image_embeddings.npy")
    output_aligned_csv_path = os.path.join(base_dir, "data", "processed", "products.csv")

    if not os.path.exists(csv_path):
        print(f"Error: Compatibility CSV not found at {csv_path}. Please run generate_metadata.py first.")
        sys.exit(1)

    print(f"Loading metadata from {csv_path}...")
    df = pd.read_csv(csv_path)
    total_products = len(df)
    print(f"Loaded {total_products} products from CSV.")

    if args.limit > 0 and args.limit < total_products:
        print(f"Limiting execution to the first {args.limit} products.")
        df = df.iloc[:args.limit]
        total_products = len(df)

    # Initialize CLIPLoader
    try:
        loader = CLIPLoader()
        model, preprocess = loader.get_model_and_preprocess()
        device = loader.get_device()
        print(f"CLIP model ready on device: {device}")
    except Exception as e:
        print(f"Failed to load CLIP model: {e}")
        sys.exit(1)

    embeddings_list = []
    aligned_products = []
    
    batch_size = args.batch_size
    start_time = time.time()
    
    # Process products in batches
    for i in range(0, total_products, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        batch_images = []
        batch_metadata = []
        
        for _, row in batch_df.iterrows():
            img_rel_path = row['primary_image']
            img_abs_path = os.path.join(data_dir, img_rel_path)
            
            if not os.path.exists(img_abs_path):
                print(f"Warning: Image file not found at {img_rel_path}. Skipping.")
                continue
                
            if not check_image_header(img_abs_path):
                print(f"Warning: Invalid or corrupted image file header at {img_rel_path}. Skipping.")
                continue
                
            try:
                # Load and preprocess
                img = Image.open(img_abs_path).convert("RGB")
                processed = preprocess(img)
                batch_images.append(processed)
                batch_metadata.append(row.to_dict())
            except Exception as e:
                print(f"Warning: Failed to load/preprocess image {img_rel_path}: {e}. Skipping.")
                continue
                
        if not batch_images:
            continue
            
        # Encode batch of images
        try:
            batch_tensor = torch.stack(batch_images).to(device)
            with torch.no_grad():
                image_features = model.encode_image(batch_tensor)
                # Normalize features to unit length (L2 norm)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                features_numpy = image_features.cpu().numpy()
                
            for emb, meta in zip(features_numpy, batch_metadata):
                embeddings_list.append(emb)
                aligned_products.append(meta)
                
            elapsed = time.time() - start_time
            rate = len(embeddings_list) / elapsed if elapsed > 0 else 0
            remaining_est = (total_products - (i + len(batch_df))) / rate if rate > 0 else 0
            print(f"Processed {len(embeddings_list)}/{total_products} | Rate: {rate:.1f} imgs/sec | Est. Remaining: {remaining_est/60:.1f} mins")
            
        except Exception as e:
            print(f"Error encoding batch starting at index {i}: {e}. Skipping batch.")
            continue

    if not embeddings_list:
        print("Error: No embeddings generated. Cannot save.")
        sys.exit(1)

    # Save aligned embeddings
    embeddings_matrix = np.array(embeddings_list).astype('float32')
    np.save(output_embeddings_path, embeddings_matrix)
    print(f"Saved {embeddings_matrix.shape[0]} embeddings of dimension {embeddings_matrix.shape[1]} to: {output_embeddings_path}")

    # Save aligned metadata CSV (excluding skipped rows)
    aligned_df = pd.DataFrame(aligned_products)
    aligned_df.to_csv(output_aligned_csv_path, index=False)
    print(f"Saved aligned metadata containing {len(aligned_df)} items to: {output_aligned_csv_path}")
    print(f"Total skipped/corrupted products: {total_products - len(aligned_df)}")

if __name__ == "__main__":
    generate_embeddings()
