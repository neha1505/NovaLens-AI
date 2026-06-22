import os
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger("novalens.llm_service")

class LLMService:
    def __init__(self):
        # Manually load .env from workspace root if it exists
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            # Strip whitespaces and quotes
                            os.environ[key.strip()] = val.strip().strip("'").strip('"')
            except Exception as e:
                logger.error(f"Failed to manually load .env file: {e}")

        # Configure LLM provider
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        # Load API keys and configurations
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.claude_key = os.getenv("CLAUDE_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
        
        # Default models for each provider
        self.gemini_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.openai_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.claude_model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20240620")


    async def generate_response(
        self, 
        system_instruction: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7
    ) -> str:
        """
        Sends system instructions and conversation history to the configured LLM provider
        and returns the generated assistant text.
        """
        if self.provider == "gemini":
            return await self._call_gemini(system_instruction, messages, temperature)
        elif self.provider == "openai":
            return await self._call_openai(system_instruction, messages, temperature)
        elif self.provider == "claude":
            return await self._call_claude(system_instruction, messages, temperature)
        else:
            # Fallback mock/error message if provider is unsupported or misconfigured
            logger.error(f"Unsupported LLM provider: {self.provider}")
            return "Configuration Error: Unsupported or misconfigured LLM provider."

    async def _call_gemini(
        self, 
        system_instruction: str, 
        messages: List[Dict[str, str]], 
        temperature: float
    ) -> str:
        if not self.gemini_key:
            # Look up standard GEMINI_API_KEY. If still empty, try to give a clean user warning
            raise ValueError("GEMINI_API_KEY is not configured in the environment.")

        # Sequence of models to try in case of rate limits (429) or high demand (503) errors
        models_to_try = [self.gemini_model]
        for fallback in ["gemini-flash-latest", "gemini-flash-lite-latest"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            
            # Convert messages to Gemini API format (user / model roles)
            contents = []
            for msg in messages:
                role = "model" if msg["role"] in ("assistant", "model") else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
                
            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": system_instruction}]
                },
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 4096
                }
            }
            
            headers = {"Content-Type": "application/json"}
            
            try:
                logger.info(f"Attempting Gemini generation using model: {model}")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        logger.info(f"Successfully generated response using model: {model}")
                        return text
                    elif response.status_code in (429, 503):
                        logger.warning(f"Gemini API returned error {response.status_code} for model {model}. Trying fallback...")
                        last_error = RuntimeError(f"Gemini API request failed for model {model}: {response.text}")
                        continue
                    else:
                        logger.error(f"Gemini API returned error {response.status_code} for model {model}: {response.text}")
                        last_error = RuntimeError(f"Gemini API request failed for model {model}: {response.text}")
                        continue
            except Exception as e:
                logger.error(f"Failed to generate response using model {model}: {e}")
                last_error = e
                continue

        raise last_error if last_error else RuntimeError("Failed to generate response from all available Gemini models.")


    async def _call_openai(
        self, 
        system_instruction: str, 
        messages: List[Dict[str, str]], 
        temperature: float
    ) -> str:
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY is not configured in the environment.")

        url = "https://api.openai.com/v1/chat/completions"
        
        openai_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            role = "assistant" if msg["role"] == "model" else msg["role"]
            openai_messages.append({"role": role, "content": msg["content"]})
            
        payload = {
            "model": self.openai_model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"OpenAI API returned error {response.status_code}: {response.text}")
                raise RuntimeError(f"OpenAI API request failed: {response.text}")
                
            result = response.json()
            try:
                return result["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse OpenAI response structure: {result}. Error: {e}")
                raise RuntimeError("Failed to parse assistant response from OpenAI.")

    async def _call_claude(
        self, 
        system_instruction: str, 
        messages: List[Dict[str, str]], 
        temperature: float
    ) -> str:
        if not self.claude_key:
            raise ValueError("CLAUDE_API_KEY is not configured in the environment.")

        url = "https://api.anthropic.com/v1/messages"
        
        claude_messages = []
        for msg in messages:
            role = "assistant" if msg["role"] in ("assistant", "model") else "user"
            claude_messages.append({"role": role, "content": msg["content"]})
            
        payload = {
            "model": self.claude_model,
            "system": system_instruction,
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        headers = {
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Claude API returned error {response.status_code}: {response.text}")
                raise RuntimeError(f"Claude API request failed: {response.text}")
                
            result = response.json()
            try:
                return result["content"][0]["text"]
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse Claude response structure: {result}. Error: {e}")
                raise RuntimeError("Failed to parse assistant response from Claude.")
