from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[0]
ENV_PATH = BACKEND_DIR / ".env"
PLACEHOLDER_API_KEYS = {"", "你的模型平台 Key", "your-api-key", "YOUR_API_KEY"}


def api_key_is_missing(api_key: str | None) -> bool:
    """判断模型 Key 是否缺失或仍是课程占位值。"""

    # 占位 Key 要当成未配置处理，不能让它一路打到模型平台才失败。
    return api_key is None or api_key.strip() in PLACEHOLDER_API_KEYS
