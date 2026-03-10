import os
import json
import itertools
from time import sleep
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv
from loguru import logger

try:
    from .rag_knowledge import rag_kb
except ImportError:
    rag_kb = None

# Load from backend/.env if exists, or root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../backend/.env"))

class AIVisionService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AIVisionService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'): return
        
        # 1. Parse Keys
        keys_str = os.getenv("GEMINI_API_KEYS")
        if not keys_str:
             # Fallback to single key
             keys_str = os.getenv("GEMINI_API_KEY")
        
        if not keys_str:
             logger.error("No GEMINI_API_KEYS found in environment.")
             self.api_keys = []
             return

        self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        self.key_cycle = itertools.cycle(self.api_keys)
        self.current_key = next(self.key_cycle)
        self._configure_client(self.current_key)
        self.initialized = True

    def _configure_client(self, key):
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def _rotate_key(self):
        if len(self.api_keys) <= 1: return False
        self.current_key = next(self.key_cycle)
        logger.warning(f"Rotate Key: Switching to next available key.")
        self._configure_client(self.current_key)
        return True

    def find_element(self, screenshot_path: str, instruction: str) -> dict:
        if not self.api_keys: return {"found": False, "error": "No API keys configured."}
        
        with open(screenshot_path, "rb") as image_file:
            image_data = image_file.read()
        
        prompt = f"""
        You are an Automation Testing Agent.
        Look at this screenshot of a web application.
        I need to interact with the element described as: "{instruction}".
        
        Please return a strictly valid JSON object with:
        "thought_process": analysis,
        "coordinates": {{ "x": <int>, "y": <int> }} (center of element).
        
        If not found, set "found": false.
        Return raw JSON only.
        """

        for attempt in range(len(self.api_keys) * 2):
            try:
                response = self.model.generate_content([
                    {'mime_type': 'image/png', 'data': image_data},
                    prompt
                ])
                res = self._parse_json(response.text)
                if res.get("thought_process"):
                    logger.info(f"🧠 AI Thoughts: {res['thought_process']}")
                return res
            except ResourceExhausted:
                if not self._rotate_key(): break
                sleep(1)
            except Exception as e:
                logger.error(f"AI Vision Error: {e}")
                break
        return {"found": False}

    def find_element_som(self, screenshot_path: str, instruction: str, som_data: dict) -> dict:
        """
        Hybrid SOM (Set-of-Mark) approach with Context Awareness.
        """
        if not self.api_keys: return {"found": False, "error": "No API keys."}
        
        with open(screenshot_path, "rb") as image_file:
            image_data = image_file.read()
        
        # 1. Format Context
        context = som_data.get("context", {})
        ctx_str = f"Active Drawer: {context.get('drawer_title') if context.get('is_drawer_open') else 'None'}"
        
        # 2. Format Labels: Prioritize foreground elements, then background, up to 100 total.
        elements = som_data.get('elements', [])
        foreground = [e for e in elements if e.get('context') == 'foreground_drawer']
        background = [e for e in elements if e.get('context') != 'foreground_drawer']
        
        # Combine them (foreground first)
        ordered_elements = foreground + background
        map_context = "\n".join([f"ID {item['id']}: role={item['role']}, text={item['text']}, placeholder={item['placeholder']}, context={item['context']}" for item in ordered_elements[:100]])

        goal_desc = f'Interact with "{instruction}"'
        if "description" in som_data:
             goal_desc += f' (Target Goal: {som_data["description"]})'
             
        retrieved_knowledge = "None"
        if rag_kb:
            # Query knowledge base with task instruction + target goal context
            retrieved_knowledge = rag_kb.query(goal_desc, top_k=2)
             
        history_str = "None"
        if som_data.get("history"):
            history_list = [f"Step '{k}' with params {v}" for k, v in som_data["history"]]
            # keep last 7 steps to not overload context
            history_str = "\n".join(history_list[-7:])
             
        prompt = f"""
        You are an Advanced QA Automation Agent testing the "Pear" system.
        Business Context: Pear is a hybrid B2C and B2B social commerce platform with a mobile-first interface. Modules include Explore (consumer feed), Events (creator/B2B management), Shops, and Posts conventions.
        You have full context of what has been executed so far, so please DO NOT repeat completed steps if the current page looks wrong.
        
        Current Page Context: {ctx_str}
        Overall Test Goal: {goal_desc}
        
        Recent Execution History (Steps ALREADY completed successfully):
        {history_str}
        
        System Training Context (RAG Knowledge):
        {retrieved_knowledge}
        
        Look at this screenshot. Interactive elements have RED numbered labels.
        Labels Metadata:
        {map_context}
        
        Task:
        1. Diagnose the current page state. Look for:
           - Are we on the correct page for the goal? (e.g. if the goal is related to Events management, we should NOT be on the Explore page).
           - Error messages (red text like "Required", "Invalid").
           - Blocking modals or popups.
           - Crucially: Check if the target element is DISABLED or grayed out.
        2. Analyze based on the History:
           - If a previous step logically brought you here, but it's the wrong page, DO NOT try to re-do a previous step like "Create Post" just because a similar button exists here. You must RECOVER (e.g., click a back button or close button to return to the right flow).
        3. Determine the NEXT logical action:
           - If the target is visible and enabled, output GOAL_CLICK.
           - If you must clear a modal or navigate away from an incorrect page (like the Explore feed), output RECOVERY_CLICK and select the appropriate label (e.g., "Back", "Close", "Cancel").
           - If you need to fill a missing field or select a precondition item, output PRECONDITION_ACTION.
           
        Return strictly valid JSON:
        {{
          "consciousness_diagnosis": "Detailed diagnosis considering the History, business context, and current visual state.",
          "thought_process": "Explain logic for picking the label_id, actively referencing WHY the history makes this the right move.",
          "suggested_action": "RECOVERY_CLICK, GOAL_CLICK, PRECONDITION_ACTION",
          "label_id": <int> or null
        }}
        """

        for attempt in range(len(self.api_keys) * 2):
            try:
                logger.info(f"Connecting to Gemini (Attempt {attempt+1})...")
                response = self.model.generate_content([
                    {'mime_type': 'image/png', 'data': image_data},
                    prompt
                ])
                logger.info(f"Gemini Raw Response: {response.text}")
                res = self._parse_json(response.text)
                if res.get("thought_process"):
                    logger.info(f"🧠 AI SOM Thoughts: {res['thought_process']}")
                return res
            except ResourceExhausted:
                if not self._rotate_key(): break
                sleep(1)
            except Exception as e:
                logger.error(f"AI Vision SOM Error: {e}")
                break
        return {"found": False}

    def _parse_json(self, text):
        try:
            raw = text.strip().replace("```json", "").replace("```", "")
            return json.loads(raw)
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}. Raw response: {text[:200]}")
            return {"found": False, "error": "Invalid AI JSON"}

# Global instance
ai_vision = AIVisionService()
