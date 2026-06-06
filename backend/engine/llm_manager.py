"""LLM 调用管理：Ollama DeepSeek"""

import requests

from config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT_SECONDS


class LLMError(Exception):
    """LLM 调用异常，携带降级消息供上层使用"""
    def __init__(self, message: str, fallback: str = "AI 服务暂不可用，请稍后再试或联系管理员。"):
        super().__init__(message)
        self.fallback = fallback


class LLMManager:
    """LLM 推理管理"""

    def generate(self, prompt: str) -> str:
        """调用 DeepSeek 生成回答，失败时抛出 LLMError"""
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
            result = data.get("response", "").strip()
            if not result:
                raise LLMError("LLM 返回空响应", fallback="AI 服务返回空结果，请稍后再试。")
            return result
        except requests.Timeout:
            raise LLMError(f"LLM 请求超时 (>{LLM_TIMEOUT_SECONDS}s)", fallback="AI 服务响应超时，请稍后再试或提交工单。")
        except requests.ConnectionError:
            raise LLMError("无法连接 LLM 服务", fallback="AI 服务连接失败，请检查服务状态或提交工单。")
        except requests.HTTPError as e:
            raise LLMError(f"LLM 服务返回错误: {e.response.status_code}", fallback="AI 服务异常，请稍后再试。")
        except LLMError:
            raise
        except Exception as e:
            from utils.logger import app_logger
            app_logger.error(f"LLM 未知错误: {type(e).__name__}: {e}")
            raise LLMError(f"LLM 未知错误: {type(e).__name__}: {e}")
