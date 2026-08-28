import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"

api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key is None:
    raise ValueError("请设置环境变量 ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key, base_url=ANTHROPIC_BASE_URL)

response = client.messages.create(
	model="claude-haiku",
	max_tokens=1024,
	messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "你是什么时候被训练出来的？"
                }
            ]
        }
    ],
)

print(response)
result = ""

for content in response.content:
    if content.type == 'text':
        result += content.text
    elif content.type == 'thinking':
        continue
    else:
        raise ValueError(f"Unexpected content type: {content.type}")

print(result if result else "没有返回文本内容")
