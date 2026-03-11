import os
import requests
import json
from typing import Optional


class EmergentAdapter:
    """Simple HTTP adapter for an Emergent-style LLM HTTP API.

    This is intentionally generic: set `EMERGENT_API_URL` and
    `EMERGENT_LLM_KEY` in `backend/.env`. The adapter sends a JSON
    payload with `prompt` and optional `model`. The response is
    returned as raw text for downstream parsing.
    """
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv('EMERGENT_API_URL')
        self.api_key = api_key or os.getenv('EMERGENT_LLM_KEY')
        if not self.api_url or not self.api_key:
            raise RuntimeError('Emergent API URL/key not configured')

    def send(self, prompt: str, model: Optional[str] = None, timeout: int = 30) -> str:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {'prompt': prompt}
        if model:
            payload['model'] = model

        resp = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        # return raw text; caller will attempt JSON parse
        return resp.text
