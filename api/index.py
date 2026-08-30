import os
import sys

# Ensure project root is in python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app

# Export app for Vercel Serverless Functions
app = app
