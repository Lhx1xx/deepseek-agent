# 🤖 DeepSeek AI 智能体

一个基于 DeepSeek 大模型、带工具调用能力的 AI 智能体，拥有网页界面（Gradio）。

## 能做什么

- 💬 对话：基于 DeepSeek 回答各类问题
- 📄 文件读写：读取、写入、列出本地文件
- 🔍 网页搜索：抓取 Bing 搜索结果，获取最新信息
- 📚 知识库检索（RAG）：基于本地文档语义检索，回答私有资料相关问题
- ⚙️ 执行命令：运行 shell 命令（默认关闭，需手动开启）

模型会**自动判断**什么时候该调用哪个工具，多步任务也能自己拆解完成。

## 项目结构

```
agent/
├── main.py              # 入口：启动 Gradio 网页
├── agent.py             # 核心：Agent 循环（调模型→执行工具→回填→循环）
├── llm.py               # DeepSeek 封装（OpenAI 兼容接口）
├── config.py            # 读取 .env 配置
├── rag.py               # RAG 引擎：向量化 + 知识库语义检索
├── knowledge_base/      # 放你要让 AI 读懂的私有文档
├── tools/
│   ├── __init__.py      # 工具定义 + 分发
│   ├── file_tools.py    # 读/写/列目录
│   ├── web_search.py    # Bing 搜索
│   └── shell_tools.py   # 执行命令
├── .env                 # 存放 API key（不要提交到 git）
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

在 PyCharm 中打开本项目，或命令行进入 `D:\agent`，然后：

```bash
pip install -r requirements.txt
```

> 建议先用 conda 建一个虚拟环境再装，避免污染全局环境：
> ```bash
> conda create -n agent python=3.11 -y
> conda activate agent
> pip install -r requirements.txt
> ```

### 2. 填入 API key

编辑 `.env` 文件，把 DeepSeek key 填进去：

```
DEEPSEEK_API_KEY=sk-你的key
```

key 到 https://platform.deepseek.com 申请。

### 3. 运行

```bash
python main.py
```

启动后终端会显示一个本地网址（如 `http://127.0.0.1:7860`），浏览器打开即可对话。

## 使用示例

- 「帮我搜索一下最新的 AI 新闻」
- 「列出当前目录下的文件」
- 「读取 D:\agent\README.md 的内容」
- 「写一个 hello.txt 文件，内容是 你好世界」
- 「根据我的知识库，这个项目用了什么技术栈？」（需先放文档进 knowledge_base）
- 勾选「允许执行命令」后：试试「帮我查一下当前目录的 python 版本」

## 知识库检索（RAG）

智能体支持基于你的本地文档回答问题：

1. 把 `.txt` / `.md` / `.pdf` 文件放进 `knowledge_base/` 目录
2. 启动 Ollama 并拉取向量模型（只需一次）：
   ```bash
   ollama pull nomic-embed-text
   ```
3. 运行时向智能体提问，例如「根据我的知识库，XX 是什么？」

首次检索会自动建立索引（向量化 + 缓存到磁盘），之后文件没变就直接读缓存。文档修改后索引会自动重建。

## 注意

- **执行命令有风险**：`run_command` 会真的在电脑上执行命令，默认关闭。开启前请确认你信任当前对话内容。
- 网页搜索走的是 Bing 抓取，偶尔可能被反爬导致无结果，换个关键词重试即可。
- Agent 每次最多调用模型 10 轮，防止死循环，可在 `.env` 里改 `MAX_ITERATIONS`。
