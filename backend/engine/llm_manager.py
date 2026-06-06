"""LLM 调用管理：Ollama DeepSeek"""

import requests

from config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT_SECONDS


class LLMManager:
    """LLM 推理管理"""

    def generate(self, prompt: str) -> str:
        """调用 DeepSeek 生成回答"""
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": LLM_TEMPERATURE,
                        "num_predict": LLM_MAX_TOKENS,
                    },
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except Exception as e:
            from utils.logger import app_logger
            app_logger.error(f"LLM 请求失败: {e}")
            return "AI 服务暂不可用，请稍后再试或联系管理员。"
