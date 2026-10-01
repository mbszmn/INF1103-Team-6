import json
import os
from google import genai
from google.genai import types
from logic_manager import fallback_classification

class AIManager:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.client = genai.Client()

    def analyze_ticket(
        self, 
        title: str, 
        description: str, 
        device: str = "Unknown", 
        error_message: str = "", 
        steps_attempted: str = ""
    ) -> dict:
        """
        Sends ticket inputs to Google AI Studio with strict prompt guardrails 
        and schema validation. Contains zero domain logic.
        """
        prompt = f"""
        You are an automated IT helpdesk triage engine for the Singapore Institute of Technology (SIT).

        [TICKET DETAILS]
        - Title: "{title}"
        - Device/OS: "{device}"
        - Description: "{description}"
        - Error Message: "{error_message}"
        - Steps Already Attempted: "{steps_attempted}"

        Analyze the ticket and return a valid JSON object ONLY containing:
        - "category": "Network" | "Hardware" | "Software" | "Account" | "Security" | "Other"
        - "priority": "Low" | "Medium" | "High" | "Critical"
        - "confidence": float between 0.0 and 1.0
        - "summary": 1-sentence concise summary
        - "affected_system": specific system, software, or hardware component
        - "security_related": boolean (true if malware, phishing, credentials, or unauthorized access)
        - "requires_escalation": boolean (true if immediate human specialist intervention is needed)
        - "troubleshooting": list of 2-3 actionable steps tailored to the user's device and issue
        """