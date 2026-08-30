import numpy as np
from PIL import Image
from ml.clip.clip_loader import CLIPLoader

try:
    import torch
except ImportError:
    torch = None

def get_image_embedding(image: Image.Image) -> np.ndarray:
    """
    Generates a 512-dimensional CLIP image embedding for a PIL Image.
    """
    if image is None:
        raise ValueError("Provided image object cannot be None.")

    loader = CLIPLoader()
    model, preprocess = loader.get_model_and_preprocess()
    device = loader.get_device()

    if model is None or preprocess is None or torch is None:
        raise RuntimeError("CLIP PyTorch model not present in lightweight environment.")

    try:
        image_input = preprocess(image).unsqueeze(0).to(device)
    except Exception as e:
        raise ValueError(f"Failed to preprocess image for CLIP: {e}")

    with torch.no_grad():
        try:
            image_features = model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            raise RuntimeError(f"Error encoding image to CLIP embedding: {e}")
