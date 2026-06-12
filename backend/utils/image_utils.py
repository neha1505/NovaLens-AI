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
