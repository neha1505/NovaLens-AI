# NovaLens AI (Phase 1: Image Retrieval System)

> [!NOTE]
> **Project Status:** Currently fully working and functional. Additional features and modifications are yet to come!

NovaLens AI is a multimodal product discovery platform for e-commerce. This is the **Phase 1** implementation, which realizes a complete visual (image-based) product similarity search engine.

When a user uploads a product image:
1. The FastAPI backend pre-processes the image and generates a 512-dimensional vector embedding using OpenAI's **CLIP** model.
2. The system executes a vector similarity query against a **FAISS** index.
3. The closest matching product items are retrieved using Cosine Similarity (Inner Product on normalized vectors).
4. Ranked results (top 10 matches) are served to a responsive, premium glassmorphic React frontend.

---

## Project Structure

```
NovaLens-AI/
├── backend/
│   ├── main.py                  # FastAPI server entry point, static image serving
│   ├── routes/
│   │   └── image_search.py       # POST /image-search endpoint
│   ├── schemas/
│   │   └── product_schema.py     # Pydantic data schemas
│   ├── services/
│   │   └── image_search_service.py # FAISS search and product mapping logic
│   └── utils/
│       └── image_utils.py        # Image validation and PIL loading
├── data/
│   ├── products.csv              # Catalog metadata mapping
│   └── images/                   # Store catalog product images
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ImageUpload.jsx   # Drag & drop upload zone with preview
│   │   │   ├── ProductCard.jsx   # Individual visual result representation
│   │   │   └── SearchResults.jsx # Results grid list and loading skeletons
│   │   ├── pages/
│   │   │   └── Home.jsx          # Dashboard and orchestration logic
│   │   ├── services/
│   │   │   └── api.js            # Axios endpoint request client
│   │   ├── App.jsx               # App wrapper
│   │   └── main.jsx              # React mounting root
│   ├── index.html
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── ml/
│   └── clip/
│       ├── clip_loader.py        # Cached singleton loading of CLIP
│       └── image_embedding.py    # Vector generator & normalizer
├── vector_store/
│   ├── build_image_index.py      # Script to compute and save vector index
│   ├── image_faiss.index         # FAISS FlatIP index database
│   └── image_metadata.pkl        # Serialized product metadata matching order
├── requirements.txt              # Backend python packages
└── README.md                     # Setup and usage guide
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git (required to build the CLIP repository wheel)

---

### Step 1: Dataset Preparation

1. Download the Kaggle **Fashion Product Images (Small)** dataset.
2. Extract and place the dataset folder inside `data/` as:
   ```
   data/fashion_dataset/
   ├── images/
   └── styles.csv
   ```
   *(Note: In the current development environment, the dataset is already present at `data/fashion/`.)*

3. Run the preparation script to validate records, check images, generate realistic prices, and create the clean `data/products.csv`:
   ```bash
   python data/prepare_dataset.py
   ```

---

### Step 2: Indexing & CLIP Embedding Generation

1. Build/rebuild the FAISS vector index from the prepared products database:
   ```bash
   python vector_store/build_image_index.py
   ```
   *Note: By default, this indexer processes 5,000 products for quick indexing. To index all 44,000+ products, you can pass `--limit -1`:*
   ```bash
   python vector_store/build_image_index.py --limit -1
   ```
   *On the first run, the script will automatically download the OpenAI CLIP ViT-B/32 weights (approx. 338MB) to your PyTorch cache folder.*

---

### Step 3: Running the FastAPI Backend

1. Start the Uvicorn web server from the project root:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. The API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Step 4: Running the React Frontend

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the local address displayed in the terminal (usually [http://localhost:5173](http://localhost:5173)).

---

## Verification & Testing

To verify the visual search system:
1. Open the frontend browser at [http://localhost:5173](http://localhost:5173).
2. Upload any product image from the Kaggle dataset (found inside `data/fashion/images/` or `data/fashion_dataset/images/`).
3. Click **Find Visually Similar**.
4. The system will load the image features, run FAISS similarity search, and display the top 10 visually matching products with their name, category, generated price, and similarity score.
