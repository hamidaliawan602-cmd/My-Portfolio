import os
import sys

# Make the project root importable when Vercel runs api/index.py.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app as flask_app

# Vercel looks for this top-level variable.
app = flask_app