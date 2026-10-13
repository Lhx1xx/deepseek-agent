"""DeepSeek 大模型封装（OpenAI 兼容接口）。"""
from openai import OpenAI

import config

_client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)


def chat(messages, tools=None):
    """调用 DeepSeek，返回一条 assistant message（可能是文本，也可能是 tool_calls）。

    messages: 标准 OpenAI 消息列表 [{"role": ..., "content": ...}, ...]
    tools:    工具定义列表（OpenAI function calling 格式）
    """
    kwargs = {
        "model": config.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        kwargs["tools"] = tools

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message
