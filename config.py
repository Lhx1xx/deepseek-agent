"""全局配置：从 .env 读取环境变量。"""
import os

from dotenv import load_dotenv

load_dotenv()

# DeepSeek 相关配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Agent 循环最多调用模型的轮数，防止死循环
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
