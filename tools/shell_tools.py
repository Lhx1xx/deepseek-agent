"""执行命令工具：运行 shell 命令（是否允许由 Agent 层的开关控制）。"""
import subprocess


def run_command(command: str, timeout: int = 60) -> str:
    """执行 shell 命令，返回 stdout / stderr / 退出码。"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"错误：命令执行超时（>{timeout}秒）"
    except Exception as e:
        return f"错误：命令执行失败：{e}"

    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()

    parts = []
    if out:
        parts.append(f"[stdout]\n{out}")
    if err:
        parts.append(f"[stderr]\n{err}")
    if result.returncode != 0:
        parts.append(f"[退出码] {result.returncode}")

    return "\n".join(parts) if parts else "（命令执行完成，无输出）"
