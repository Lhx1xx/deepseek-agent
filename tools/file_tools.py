"""文件读写工具：供 Agent 调用。"""
import os


def read_file(path: str) -> str:
    """读取文本文件内容，超长则截断，避免撑爆上下文。"""
    path = os.path.expanduser(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"错误：文件不存在：{path}"
    except UnicodeDecodeError:
        # UTF-8 读不了，尝试 GBK（Windows 常见中文编码）
        try:
            with open(path, "r", encoding="gbk") as f:
                content = f.read()
        except Exception as e:
            return f"错误：无法读取文件（可能是二进制文件）：{path}：{e}"
    except Exception as e:
        return f"错误：读取文件失败 {path}：{e}"

    if len(content) > 20000:
        content = content[:20000] + "\n...(内容过长，已截断)..."
    return content


def write_file(path: str, content: str) -> str:
    """把内容写入文件（覆盖写入），会自动创建父目录。"""
    path = os.path.expanduser(path)
    parent = os.path.dirname(path)
    try:
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功写入文件：{path}"
    except Exception as e:
        return f"错误：写入文件失败 {path}：{e}"


def list_dir(path: str = ".") -> str:
    """列出目录内容，返回每项的名称和类型。"""
    path = os.path.expanduser(path)
    try:
        entries = os.listdir(path)
    except Exception as e:
        return f"错误：无法列出目录 {path}：{e}"

    if not entries:
        return "（空目录）"

    lines = []
    for name in sorted(entries):
        full = os.path.join(path, name)
        tag = "[目录]" if os.path.isdir(full) else "[文件]"
        lines.append(f"{tag} {name}")
    return "\n".join(lines)
