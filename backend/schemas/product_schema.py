from pydantic import BaseModel

class ProductSearchResult(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    price: float
    similarity_score: float
    image_path: str
