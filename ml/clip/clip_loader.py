import os
import sys
import gc
import threading

if sys.platform == "win32":
    torch_lib = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
    if os.path.exists(torch_lib) and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(torch_lib)
        except Exception:
            pass

try:
    import torch
    import clip
except Exception:
    torch = None
    clip = None

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
                    if torch is None or clip is None:
                        print("Torch/CLIP not installed. Using lightweight catalog matching mode.")
                        self.model = None
                        self.preprocess = None
                        self.device = "cpu"
                        self._initialized = True
                        return None, None

                    gc.collect()
                    try:
                        torch.set_num_threads(1)
                    except Exception:
                        pass
                    
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    print(f"Loading CLIP model 'ViT-B/32' on device: {self.device}...")
                    
                    try:
                        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device, jit=False)
                        self.model.eval()
                        for p in self.model.parameters():
                            p.requires_grad = False
                    except Exception as e:
                        print(f"Warning: Model load bypassed due to memory: {e}")
                        self.model = None
                        self.preprocess = None

                    gc.collect()
                    self._initialized = True
                    
        return self.model, self.preprocess

    def get_device(self):
        return getattr(self, 'device', "cpu")
