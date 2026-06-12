import os
import sys
import pickle
import argparse
import pandas as pd
import numpy as np
import faiss
import torch
from PIL import Image

# Ensure parent directory is in python path so we can import from ml
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.clip.clip_loader import CLIPLoader

def build_index():
    parser = argparse.ArgumentParser(description="Build FAISS vector index for product images.")
    parser.add_argument('--limit', type=int, default=5000, help='Limit the number of products to index (set to -1 for all).')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for generating CLIP embeddings.')
    args = parser.parse_args()

    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "products.csv")
    data_dir = os.path.join(base_dir, "data")
    index_path = os.path.join(base_dir, "vector_store", "image_faiss.index")
    metadata_path = os.path.join(base_dir, "vector_store", "image_metadata.pkl")

    # Ensure output directories exist
    os.makedirs(os.path.join(base_dir, "vector_store"), exist_ok=True)

    # 1. Load products.csv
    if not os.path.exists(csv_path):
        print(f"Error: Products file not found at {csv_path}. Please run prepare_dataset.py first.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    
    total_available = len(df)
    limit = args.limit
    if limit <= 0 or limit > total_available:
        limit = total_available
        
    # Slice to limit
    df = df.iloc[:limit]
    print(f"Loaded {limit} products")

    # Load CLIP Loader once
    try:
        loader = CLIPLoader()
        model, preprocess = loader.get_model_and_preprocess()
        device = loader.get_device()
    except Exception as e:
        print(f"Error initializing CLIP model: {e}")
        sys.exit(1)

    print("Generating embeddings...")

    embeddings = []
    metadata = []
    
    batch_size = args.batch_size
    
    # Process images in batches
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        batch_images = []
        batch_metadata = []
        
        for _, row in batch_df.iterrows():
            product_id = row['product_id']
            image_name = row['image_path']
            image_path = os.path.join(data_dir, image_name)
            
            # Validation checks
            if not os.path.exists(image_path):
                print(f"Warning: Image file not found for product {product_id} at {image_path}. Skipping.")
                continue
                
            try:
                # Open and preprocess
                img = Image.open(image_path).convert("RGB")
                processed = preprocess(img)
                batch_images.append(processed)
                
                # Store corresponding metadata
                batch_metadata.append({
                    "product_id": str(row['product_id']),
                    "name": str(row['name']),
                    "category": str(row['category']),
                    "description": str(row['description']),
                    "price": float(row['price']),
                    "image_path": str(row['image_path'])
                })
            except Exception as e:
                print(f"Warning: Invalid image for product {product_id} at {image_path}: {e}. Skipping.")
                continue
                
        if not batch_images:
            continue
            
        # Encode batch of images
        try:
            batch_tensor = torch.stack(batch_images).to(device)
            
            with torch.no_grad():
                # Generate embeddings
                image_features = model.encode_image(batch_tensor)
                # Normalize features to unit length (L2 norm)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                # Convert to numpy array
                features_numpy = image_features.cpu().numpy()
                
            for emb, meta in zip(features_numpy, batch_metadata):
                embeddings.append(emb)
                metadata.append(meta)
                
        except Exception as e:
            print(f"Error encoding batch starting at index {i}: {e}. Skipping batch.")
            continue
            
        # Display progress tracking
        processed_count = len(embeddings)
        print(f"Processed {processed_count}/{limit}")

    if not embeddings:
        print("Error: No embeddings were generated. Cannot build index.")
        sys.exit(1)

    # Convert embeddings to float32 numpy array as required by FAISS
    embedding_matrix = np.array(embeddings).astype('float32')
    dimension = embedding_matrix.shape[1]
    
    print("Building FAISS index...")
    # IndexFlatIP (Inner Product) measures Cosine Similarity because the vectors are L2-normalized.
    index = faiss.IndexFlatIP(dimension)
    index.add(embedding_matrix)
    
    # Save index and metadata mapping
    print("Saving metadata...")
    try:
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
    except Exception as e:
        print(f"Error saving metadata: {e}")
        sys.exit(1)
        
    print("Saving index...")
    try:
        faiss.write_index(index, index_path)
    except Exception as e:
        print(f"Error saving FAISS index: {e}")
        sys.exit(1)

    print("Completed successfully.")

if __name__ == "__main__":
    build_index()
