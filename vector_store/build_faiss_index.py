import os
import numpy as np
import faiss
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def build_faiss_index():
    print("=== Building New FAISS Vector Index ===")
    
    embeddings_path = os.path.join(base_dir, "data", "processed", "image_embeddings.npy")
    index_output_path = os.path.join(base_dir, "data", "processed", "faiss.index")

    if not os.path.exists(embeddings_path):
        print(f"Error: Embeddings file not found at {embeddings_path}. Please run generate_embeddings.py first.")
        sys.exit(1)

    print(f"Loading embeddings from {embeddings_path}...")
    embeddings = np.load(embeddings_path).astype('float32')
    print(f"Loaded {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}.")

    dimension = embeddings.shape[1]
    print(f"Building FAISS IndexFlatIP with dimension {dimension}...")
    
    # Create the index
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    print(f"FAISS index built. Total indexed vectors: {index.ntotal}")
    
    # Save the index
    os.makedirs(os.path.dirname(index_output_path), exist_ok=True)
    faiss.write_index(index, index_output_path)
    print(f"Saved FAISS index to: {index_output_path}")

if __name__ == "__main__":
    build_faiss_index()
