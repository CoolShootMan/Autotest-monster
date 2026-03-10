import re
import logging

logger = logging.getLogger(__name__)

class EnterpriseTaskParser:
    """
    Implements the Dual-Mechanism design:
    Layer 1: Heuristic/Regex (Fast, Free, Deterministic)
    Layer 2: AI/LLM (Smart, Costly, Global Context) - Placeholder for now
    """

    def __init__(self, ai_api_key: str = None):
        self.ai_api_key = ai_api_key

    async def parse(self, natural_language_instruction: str) -> dict:
        """
        Parses a natural language string into a structured Playwright instruction.
        """
        logger.info(f"Parsing instruction: {natural_language_instruction}")

        # --- Layer 1: Heuristic / Regex Matcher (The "Fast Path") ---
        # Goal: Cover 80% of simple actions without spending tokens.
        
        # Pattern: "Click [Text]" or "Click the [Text] button"
        click_match = re.search(r"click\s+(?:the\s+)?['\"]?(.+?)['\"]?(?:\s+button)?$", natural_language_instruction, re.IGNORECASE)
        if click_match:
            target_text = click_match.group(1)
            return {
                "type": "heuristic",
                "action": "click",
                "locator": f"text={target_text}",  # Simple text locator
                "confidence": 0.95,
                "reasoning": "Matched simple 'click' regex pattern."
            }

        # Pattern: "Type [Value] into [Field]"
        type_match = re.search(r"(?:type|enter|fill)\s+['\"]?(.+?)['\"]?\s+(?:into|in)\s+(?:the\s+)?['\"]?(.+?)['\"]?(?:\s+field)?$", natural_language_instruction, re.IGNORECASE)
        if type_match:
            value = type_match.group(1)
            field_name = type_match.group(2)
            return {
                "type": "heuristic",
                "action": "fill",
                "locator": f"text={field_name}", # Naive, AI would improve this to input[name=...]
                "value": value,
                "confidence": 0.85,
                "reasoning": "Matched simple 'fill' regex pattern."
            }

        # --- Layer 2: AI Agent (The "Smart Fallback") ---
        # Only activated if Layer 1 fails or returns low confidence.
        if self.ai_api_key:
            return await self._call_ai_agent(natural_language_instruction)
        
        return {
            "type": "failure",
            "error": "Could not parse instruction via Heuristics, and no AI Key provided.",
            "suggestion": "Please provide an OpenAI/Gemini API key to enable Layer 2 parsing."
        }

    async def _call_ai_agent(self, instruction: str) -> dict:
        """
        Mock for the LLM call. In production, this would call GPT-4o/Gemini.
        """
        # TODO: Implement actual LangChain/OpenAI call here.
        # This would return:
        # { "action": "click", "locator": "css=button.submit-primary", "reason": "Analyzed visual context..." }
        return {
            "type": "ai_mock",
            "action": "unknown",
            "info": "AI Agent not yet implemented. Please config API Key."
        }
