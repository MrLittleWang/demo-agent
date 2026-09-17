import os
from xml.parsers.expat import model

import anthropic
from dotenv import load_dotenv
import httpx

from agent_logging import log_model_input, log_model_output
from config.setting import api_key_is_missing


load_dotenv()

api_key = os.environ["ANTHROPIC_API_KEY"]
base_url = os.environ["ANTHROPIC_BASE_URL"]
client = anthropic.Anthropic(api_key=api_key, base_url=base_url)


def call_chat_model(messages: str,  *,
    http_client: httpx.Client | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,) -> str:
    """
    调用聊天模型进行对话。

    :param user_message: 用户输入的消息
    :return: 模型生成的回答
    """
    resolved_api_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY")
    resolved_base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.siliconflow.cn/v1")).rstrip("/")
    resolved_model = model or os.getenv("AGENT_OPENAI_MODEL", "Qwen/Qwen3-8B")

    request_kwargs = {
        "headers": {"Authorization": f"Bearer {resolved_api_key}", "Content-Type": "application/json"},
        "json": {"model": "deepseek-v4-flash", "messages": messages},
    }

    log_model_input(model=resolved_model, messages=request_kwargs["json"]["messages"], prompt_source=__file__)

    if http_client is not None:
        response = http_client.post(f"{resolved_base_url}/chat/completions", **request_kwargs)
    else:
        response = httpx.post(f"{resolved_base_url}/chat/completions", **request_kwargs, timeout=30)
    response.raise_for_status()
    payload = response.json()

    log_model_output(model=resolved_model, content=payload["choices"][0]["message"]["content"])
    return payload["choices"][0]["message"]["content"]

   