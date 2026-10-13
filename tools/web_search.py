"""网页搜索工具：抓取 Bing 搜索结果。"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def web_search(query: str, num: int = 5) -> str:
    """用 Bing 搜索，返回前 num 条结果（标题 + 链接 + 摘要）。"""
    try:
        resp = requests.get(
            "https://cn.bing.com/search",
            params={"q": query, "count": num},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"错误：搜索请求失败：{e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for li in soup.select("li.b_algo"):
        a = li.select_one("h2 a")
        if not a:
            continue
        title = a.get_text(strip=True)
        url = a.get("href", "")
        snippet_el = li.select_one(".b_caption p") or li.select_one("p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= num:
            break

    if not results:
        return "未找到搜索结果（可能被反爬或网络异常），请换个关键词再试。"

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['url']}\n   {r['snippet']}")
    return "\n\n".join(lines)
