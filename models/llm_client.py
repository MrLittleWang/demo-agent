import os

import anthropic
from dotenv import load_dotenv


load_dotenv()

api_key = os.environ["ANTHROPIC_API_KEY"]
base_url = os.environ["ANTHROPIC_BASE_URL"]
client = anthropic.Anthropic(api_key=api_key, base_url=base_url)


def call_chat_model(user_message: str, session_id: str) -> str:
    """
    调用聊天模型进行对话。

    :param user_message: 用户输入的消息
    :param session_id: 会话ID，用于区分不同用户的对话历史
    :return: 模型生成的回答
    """
    history = []
    SYSTEM_PROMPT = f"""
                你是小杰电商公司的客服 Agent。当前版本只负责普通聊天，不能承诺优惠、退款、物流或售后处理结果。
                """

    history.append({"role": "user", "content": user_message})
    response = client.messages.create(model="deepseek-v4-flash",
                                          max_tokens=1024,
                                          system=SYSTEM_PROMPT,
                                          messages=history)
    return next(content.text for content in response.content if content.type == 'text')
    

   