"""入口：启动 Gradio 网页界面。"""
import gradio as gr

import config
from agent import run_agent


def respond(message, history, allow_shell):
    """Gradio 回调：接收用户输入，返回 Agent 的最终回答。"""
    if not config.DEEPSEEK_API_KEY:
        return "❌ 尚未配置 DeepSeek API key。请编辑 .env 文件，把 DEEPSEEK_API_KEY 填上后重启。"
    answer, _ = run_agent(message, history, allow_shell=allow_shell)
    return answer


demo = gr.ChatInterface(
    fn=respond,
    additional_inputs=[
        gr.Checkbox(label="⚠️ 允许执行命令（有风险，默认关闭）", value=False),
    ],
    title="🤖 DeepSeek AI 智能体",
    description=(
        "一个能读文件、写文件、搜网页、执行命令的 AI 智能体。\n"
        "试试：「帮我搜索一下最新的 AI 新闻」「列出当前目录下的文件」"
    ),
    examples=[
        ["帮我搜索一下最新的 AI 新闻", False],
        ["列出当前目录下的文件", False],
        ["读取 D:\\agent\\README.md 的内容", False],
    ],
)


if __name__ == "__main__":
    demo.launch()
