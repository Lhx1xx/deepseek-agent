"""工具注册：定义工具 schema（给模型看）+ 执行分发（给 Agent 用）。

模型通过 TOOL_SCHEMAS 知道有哪些工具、各需要什么参数；
Agent 通过 execute_tool() 实际执行并拿到结果。
"""
from . import file_tools, shell_tools, web_search

import rag

# 供模型识别的工具定义（OpenAI function calling 格式）
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文本文件的内容。当需要查看文件内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要读取的文件路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "把内容写入（覆盖）本地文件。当需要保存或生成文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要写入的文件路径"},
                    "content": {"type": "string", "description": "要写入的文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "列出目录下的文件和子目录。当需要查看目录内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要列出的目录路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "用搜索引擎搜索网络，返回若干条结果的标题、链接和摘要。当需要最新信息或外部资料时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "num": {"type": "integer", "description": "返回结果数量，默认5"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行 shell 命令并返回输出。仅在明确需要运行系统命令时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 shell 命令"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "在本地知识库（knowledge_base 目录）中检索相关内容。当用户的问题可能涉及他自己的本地资料（如简历、文档、笔记、项目说明）时，优先用这个工具检索，再基于检索到的片段回答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询，用关键词或一句话描述"},
                    "top_k": {"type": "integer", "description": "返回最相关的片段数量，默认5"},
                },
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    """根据工具名分发执行，返回字符串结果。"""
    if name == "read_file":
        return file_tools.read_file(args.get("path", ""))
    if name == "write_file":
        return file_tools.write_file(args.get("path", ""), args.get("content", ""))
    if name == "list_dir":
        return file_tools.list_dir(args.get("path", "."))
    if name == "web_search":
        return web_search.web_search(args.get("query", ""), args.get("num", 5))
    if name == "run_command":
        return shell_tools.run_command(args.get("command", ""))
    if name == "search_knowledge":
        return rag.search_knowledge(args.get("query", ""), args.get("top_k", 5))
    return f"错误：未知工具 {name}"
