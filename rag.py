"""RAG（检索增强生成）引擎：把本地知识库向量化，支持语义检索。

流程：
1. 读取 knowledge_base/ 目录下的 .txt / .md / .pdf 文件
2. 切成带重叠的小块（chunk），用 Ollama 的 nomic-embed-text 模型向量化
3. 检索时把 query 也向量化，用余弦相似度找最相关的片段
4. 向量和索引会缓存到磁盘，文件没变就不重新向量化
"""
import json
import os
from pathlib import Path

import numpy as np
import requests

# ---- 配置（可用环境变量覆盖）----
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
KB_DIR = Path(__file__).parent / "knowledge_base"
CHUNK_SIZE = 500      # 每块字符数
CHUNK_OVERLAP = 50    # 块间重叠字符数
BATCH_SIZE = 16       # 每批向量化的文本条数
CACHE_EMB = KB_DIR / ".index_embeddings.npy"
CACHE_CHUNKS = KB_DIR / ".index_chunks.json"
CACHE_SIG = KB_DIR / ".index_sig.json"

# 模块级缓存：已加载的索引 (chunks, embeddings)
_INDEX = None


# ---- 1. 向量化（Ollama）----
def _embed(texts):
    """调用 Ollama 把一批文本转成向量，返回 (n, dim) 的 float32 数组。"""
    if isinstance(texts, str):
        texts = [texts]
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        return np.array(resp.json()["embeddings"], dtype="float32")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"无法连接 Ollama（{OLLAMA_URL}）。请先启动 Ollama，并确保已执行：ollama pull {EMBED_MODEL}"
        )
    except Exception as e:
        raise RuntimeError(f"向量化失败：{e}")


# ---- 2. 读文件 + 分块 ----
def _read_text(path):
    """读 .txt / .md，自动尝试 utf-8 和 gbk 编码。"""
    for enc in ("utf-8", "gbk"):
        try:
            return Path(path).read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return ""


def _read_pdf(path):
    """用 pypdf 抽取 PDF 文本。"""
    from pypdf import PdfReader

    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _load_file(path):
    """按扩展名加载单个文件，返回文本；不支持的类型返回 None。"""
    ext = Path(path).suffix.lower()
    try:
        if ext in (".txt", ".md"):
            return _read_text(path)
        if ext == ".pdf":
            return _read_pdf(path)
    except Exception as e:
        print(f"[RAG] 读取文件失败 {path}：{e}")
    return None


def _chunk(text, source):
    """把长文本切成带重叠的小块，返回 [(来源文件名, 片段文本), ...]。"""
    text = text.strip()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(text), step):
        piece = text[i : i + CHUNK_SIZE].strip()
        if piece:
            chunks.append((source, piece))
    return chunks


def _list_files():
    """列出知识库目录下所有支持的文件（排除隐藏文件和缓存文件）。"""
    if not KB_DIR.exists():
        return []
    supported = {".txt", ".md", ".pdf"}
    return [
        p
        for p in sorted(KB_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in supported and not p.name.startswith(".")
    ]


def _signature(files):
    """根据 (路径, 修改时间, 大小) 生成签名，用于判断缓存是否失效。"""
    return [(str(p), int(p.stat().st_mtime), p.stat().st_size) for p in files]


# ---- 3. 建索引 / 读写缓存 ----
def _build_index(files):
    """读取所有文件、分块、向量化，返回 (chunks, 归一化后的 embeddings)。"""
    chunks = []
    for f in files:
        text = _load_file(f)
        if text:
            chunks.extend(_chunk(text, f.name))

    if not chunks:
        return [], np.zeros((0, 0), dtype="float32")

    embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_texts = [t for _, t in chunks[i : i + BATCH_SIZE]]
        embeddings.append(_embed(batch_texts))

    emb = np.vstack(embeddings)
    # 归一化，检索时直接用点积算余弦相似度
    emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
    return chunks, emb


def _save_cache(chunks, embeddings, sig):
    KB_DIR.mkdir(parents=True, exist_ok=True)
    np.save(CACHE_EMB, embeddings)
    CACHE_CHUNKS.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    CACHE_SIG.write_text(json.dumps(sig), encoding="utf-8")


def _load_cache():
    chunks = json.loads(CACHE_CHUNKS.read_text(encoding="utf-8"))
    embeddings = np.load(CACHE_EMB)
    return chunks, embeddings


def ensure_index():
    """确保索引已加载：优先用磁盘缓存，文件变了就重建。"""
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    files = _list_files()
    if not files:
        _INDEX = ([], None)
        return _INDEX

    sig = _signature(files)
    try:
        if json.loads(CACHE_SIG.read_text(encoding="utf-8")) == sig:
            chunks, embeddings = _load_cache()
            _INDEX = (chunks, embeddings)
            return _INDEX
    except (FileNotFoundError, ValueError):
        pass

    print(f"[RAG] 正在为 {len(files)} 个文件建立索引...")
    chunks, embeddings = _build_index(files)
    _save_cache(chunks, embeddings, sig)
    _INDEX = (chunks, embeddings)
    print(f"[RAG] 索引完成，共 {len(chunks)} 个片段。")
    return _INDEX


def rebuild_index():
    """清空缓存并重建索引（知识库新增/修改文件后调用）。"""
    global _INDEX
    _INDEX = None
    return ensure_index()


# ---- 4. 检索 ----
def search_knowledge(query, top_k=5):
    """在知识库中检索与 query 最相关的片段，返回格式化文本。"""
    chunks, embeddings = ensure_index()
    if embeddings is None or embeddings.shape[0] == 0:
        return "知识库为空：请在 knowledge_base/ 目录放入 .txt/.md/.pdf 文件后重试。"

    try:
        qv = _embed(query)[0]
    except RuntimeError as e:
        return str(e)

    qv = qv / (np.linalg.norm(qv) + 1e-9)
    sims = embeddings @ qv  # (n,)
    top_idx = np.argsort(sims)[::-1][:top_k]

    lines = []
    for rank, idx in enumerate(top_idx, 1):
        src, text = chunks[idx]
        lines.append(f"[片段{rank}｜来源:{src}｜相关度:{float(sims[idx]):.3f}]\n{text}")
    return "\n\n".join(lines)
