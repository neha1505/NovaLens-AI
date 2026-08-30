import gc
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
        pass

    def get_model_and_preprocess(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    gc.collect()
                    try:
                        torch.set_num_threads(1)
                    except Exception:
                        pass
                    
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    print(f"Loading CLIP model 'ViT-B/32' on device: {self.device}...")
                    
                    # Load model with jit=False and disable gradients to minimize RAM overhead
                    self.model, self.preprocess = clip.load("ViT-B/32", device=self.device, jit=False)
                    self.model.eval()
                    for p in self.model.parameters():
                        p.requires_grad = False
                    
                    gc.collect()
                    self._initialized = True
                    print("CLIP model loaded successfully with memory optimization.")
                    
        return self.model, self.preprocess

    def get_device(self):
        return getattr(self, 'device', "cpu")
