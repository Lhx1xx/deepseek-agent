"""Agent 核心：循环调用模型、执行工具，直到得到最终答案。"""
import json

import config
import llm
from tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = (
    "你是一个能干、谨慎的 AI 智能体助手，可以调用工具来完成用户的请求。\n"
    "可用工具：read_file（读文件）、write_file（写文件）、list_dir（列目录）、"
    "web_search（网络搜索）、search_knowledge（检索本地知识库）、run_command（执行命令）。\n"
    "使用规则：\n"
    "1. 需要最新信息或外部资料时用 web_search；需要查看/保存文件时用文件工具；"
    "用户的问题涉及他自己的本地资料（如简历、文档、笔记）时，优先用 search_knowledge 检索知识库；"
    "只有确实需要运行系统命令时才用 run_command。\n"
    "2. 先调用工具获取真实信息，再基于结果回答，不要凭空编造。\n"
    "3. 用中文回答，除非用户要求其他语言。\n"
    "4. 如果工具返回错误，尝试换一种方式，或如实告诉用户。"
)


def _build_messages(user_input: str, history: list) -> list:
    """把 Gradio 传入的历史 + 用户输入，组装成 OpenAI 消息列表。

    Gradio 6 的 history 是一串扁平的消息字典：
    [{"role": "user"/"assistant", "content": ...}, ...]
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history or []:
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
        elif hasattr(item, "role") and hasattr(item, "content"):
            role, content = item.role, item.content
        else:
            continue
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": user_input})
    return messages


def run_agent(user_input: str, history: list, allow_shell: bool = False):
    """执行一次 Agent 对话。

    history: Gradio 传入的历史（扁平消息字典列表）
    allow_shell: 是否允许模型执行 run_command 工具（默认关闭，安全起见）
    返回: (最终答案, 工具调用步骤列表)
    """
    messages = _build_messages(user_input, history)

    steps = []

    for _ in range(config.MAX_ITERATIONS):
        message = llm.chat(messages, TOOL_SCHEMAS)

        # 模型要调用工具
        if message.tool_calls:
            # 把 assistant 的 tool_calls 消息原样加回上下文
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            for tc in message.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                print(f"[工具调用] {name}({json.dumps(args, ensure_ascii=False)})")

                if name == "run_command" and not allow_shell:
                    result = "错误：执行命令功能未启用，请在界面上勾选「允许执行命令」后再试。"
                else:
                    result = execute_tool(name, args)

                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
                steps.append(f"{name}({json.dumps(args, ensure_ascii=False)})")

        # 模型给出最终回答
        else:
            return message.content or "（无回答）", steps

    return "已达到最大调用轮数，任务可能太复杂，请拆解后再试。", steps
