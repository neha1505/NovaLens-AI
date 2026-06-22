from PIL import Image
import io
from fastapi import UploadFile, HTTPException

def validate_and_load_image(file: UploadFile) -> Image.Image:
    """
    Validates that the uploaded file is a valid image format and loads it into PIL.
    """
    # 1. Verify content type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only JPEG, PNG, JPG, and WEBP are supported."
        )

    # 2. Try loading as PIL Image
    try:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        image = Image.open(io.BytesIO(content))
        image.verify()  # Verify it is an image
        
        # Re-open because verify() closes the stream and breaks subsequent operations
        file.file.seek(0)
        content = file.file.read()
        image = Image.open(io.BytesIO(content))
        return image
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decode image. Ensure the file is not corrupted. Error: {str(e)}"
        )


def is_valid_product_image(url: str) -> bool:
    """
    Validates a product image URL or path.
    Rejects placeholders, sprites, segment masks, and extremely small local images.
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Reject placeholders, sprites, dummy, loading, transparent, icon, avatar, default, segment/silhouette
    reject_keywords = [
        "placeholder", "sprite", "dummy", "loading", "transparent", 
        "icon", "avatar", "default", "silhouette", "segment", "mask",
        "pixel", "blank", "spacer", "no-image", "noimage", "not-found", 
        "notfound", "grey-box", "gray-box"
    ]
    for kw in reject_keywords:
        if kw in url_lower:
            return False
            
    # Check dimensions for local files
    if not url.startswith("http") and not url.startswith("data:"):
        import os
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        possible_paths = [
            url,
            os.path.join(base_dir, url),
            os.path.join(base_dir, "data", url),
            os.path.join(base_dir, "data", "DeepFashion", url),
        ]
        resolved_path = None
        for p in possible_paths:
            if os.path.exists(p) and os.path.isfile(p):
                resolved_path = p
                break
                
        if resolved_path:
            try:
                with Image.open(resolved_path) as img:
                    width, height = img.size
                    if width < 50 or height < 50:
                        return False
            except Exception:
                return False
                
    return True
