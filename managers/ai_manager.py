import json
import os
from google import genai
from google.genai import types
from logic_manager import fallback_classification

class AIManager:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.client = genai.Client()