import torch
import clip
import threading

class CLIPLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CLIPLoader, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading CLIP model 'ViT-B/32' on device: {self.device}")
        
        try:
            # Load the ViT-B/32 model
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            self.model.eval()  # Set model to evaluation mode
            self._initialized = True
            print("CLIP model loaded successfully.")
        except Exception as e:
            print(f"Error loading CLIP model: {e}")
            raise e

    def get_model_and_preprocess(self):
        if not self._initialized:
            raise RuntimeError("CLIP model has not been successfully initialized.")
        return self.model, self.preprocess

    def get_device(self):
        return self.device
