"""Minimal OpenAI-compatible chat completion client (targets OpenRouter)."""

import os
import time

import requests


class ModelClient:
    def __init__(self, config: dict):
        model_cfg = config["model"]
        self.api_base = model_cfg["api_base"].rstrip("/")
        api_key_env = model_cfg["api_key_env"]
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise RuntimeError(
                f"Missing API key: set ${api_key_env} (see config.yaml -> model.api_key_env)."
            )
        self.timeout_s = model_cfg.get("request_timeout_s", 60)
        self.max_retries = model_cfg.get("max_retries", 3)

    def chat(self, model: str, messages: list[dict], temperature: float, max_tokens: int) -> tuple[str, dict]:
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agent-skill-poc",
            "X-Title": "agent-skill-poc",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_s)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"] or ""
                usage = data.get("usage", {}) or {}
                return text, usage
            except Exception as e:  # noqa: BLE001 - retry on any transient failure
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Model request failed after {self.max_retries} attempts: {last_err}")
