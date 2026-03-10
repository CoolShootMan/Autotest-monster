import os
import logging
import base64
import json
import itertools
from time import sleep
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIVisionService:
    def __init__(self):
        # 1. Parse Keys
        keys_str = os.getenv("GEMINI_API_KEYS")
        if not keys_str:
            raise ValueError("GEMINI_API_KEYS not found in .env. Expected comma-separated list.")
        
        self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if not self.api_keys:
            raise ValueError("No valid API keys found in GEMINI_API_KEYS.")

        logger.info(f"Loaded {len(self.api_keys)} Gemini API Keys.")
        
        # 2. Setup Round-Robin Iterator
        self.key_cycle = itertools.cycle(self.api_keys)
        self.current_key = next(self.key_cycle)
        self._configure_client(self.current_key)

    def _configure_client(self, key):
        genai.configure(api_key=key)
        # Use Gemini 3 Flash Preview as requested by user
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def _rotate_key(self):
        old_key = self.current_key
        self.current_key = next(self.key_cycle)
        logger.warning(f"Rotate Key: Switching from ...{old_key[:4]} to ...{self.current_key[:4]}")
        self._configure_client(self.current_key)

    def find_element(self, screenshot_path: str, instruction: str) -> dict:
        """
        Analyzes a screenshot to find the element described by 'instruction'.
        Retries with key rotation if Rate Limit (429) is hit.
        """
        logger.info(f"AI Vision analyzing: '{instruction}'")
        
        # Load image
        with open(screenshot_path, "rb") as image_file:
            image_data = image_file.read()
        
        prompt = f"""
        You are an Automation Testing Agent.
        Look at this screenshot of a web application.
        I need to interact with the element described as: "{instruction}".
        
        Please return a strictly valid JSON object with the following fields:
        1. "thought_process": A brief analysis of where the element is.
        2. "suggested_locator": A Playwright-compatible selector (e.g., "text=Submit", "css=.btn-primary") if clearly visible.
        3. "coordinates": {{ "x": <int>, "y": <int> }} representing the CENTER of the element.
        
        If you cannot find it, set "found": false.
        Do NOT wrap the JSON in markdown code blocks. Just return the raw JSON string.
        """

        # Retry Loop (at most 1 attempt per key to avoid infinite loops)
        max_retries = len(self.api_keys) * 2 
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content([
                    {'mime_type': 'image/png', 'data': image_data},
                    prompt
                ])
                return self._parse_response(response)

            except ResourceExhausted:
                logger.error(f"Quota Exceeded on key ...{self.current_key[:4]}. Rotating...")
                self._rotate_key()
                # Short backoff
                sleep(1)
                continue
            
            except Exception as e:
                logger.error(f"AI Error: {e}")
                return {"found": False, "error": str(e)}

        return {"found": False, "error": "All API keys exhausted or failed."}

    def _parse_response(self, response) -> dict:
        try:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            result = json.loads(raw_text)
            logger.info(f"AI Response: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Raw Response: {response.text}")
            return {"found": False, "error": str(e)}

if __name__ == "__main__":
    pass
