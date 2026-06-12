import torch
from PIL import Image
import numpy as np
from ml.clip.clip_loader import CLIPLoader

def get_image_embedding(image_input) -> np.ndarray:
    """
    Generates a normalized CLIP embedding for a given image input.
    
    Args:
        image_input: Either an absolute string file path to an image or a PIL.Image object.
        
    Returns:
        np.ndarray: A 1D numpy array representing the normalized CLIP embedding (dimension 512).
    """
    # Load image if it's a file path
    if isinstance(image_input, str):
        try:
            image = Image.open(image_input).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to open image from path '{image_input}': {e}")
    elif isinstance(image_input, Image.Image):
        image = image_input.convert("RGB")
    else:
        raise TypeError("image_input must be a file path (str) or a PIL Image object.")

    # Get model and preprocess function from CLIPLoader
    loader = CLIPLoader()
    model, preprocess = loader.get_model_and_preprocess()
    device = loader.get_device()

    # Preprocess image and move tensor to correct device
    try:
        processed_image = preprocess(image).unsqueeze(0).to(device)
    except Exception as e:
        raise RuntimeError(f"Failed to preprocess image: {e}")

    # Generate embedding
    with torch.no_grad():
        try:
            # clip model encodes image to features
            image_features = model.encode_image(processed_image)
            # L2 Normalize the features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            # Convert to numpy array and flatten/extract vector
            embedding = image_features.cpu().numpy().flatten()
            return embedding
        except Exception as e:
            raise RuntimeError(f"Error encoding image to CLIP embedding: {e}")
