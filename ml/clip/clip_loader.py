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
                cls._instance.model = None
                cls._instance.preprocess = None
            return cls._instance

    def __init__(self):
        # Lazy initialization to prevent startup timeouts on cloud deployments
        pass

    def get_model_and_preprocess(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    try:
                        torch.set_num_threads(2)
                    except Exception:
                        pass
                    
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    print(f"Loading CLIP model 'ViT-B/32' on device: {self.device}...")
                    
                    self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
                    self.model.eval()
                    self._initialized = True
                    print("CLIP model loaded successfully.")
                    
        return self.model, self.preprocess

    def get_device(self):
        return getattr(self, 'device', "cpu")
