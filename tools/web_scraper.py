"""
网页内容抓取工具 — 基于 Scrapling
让 Agent 不只是看搜索摘要，而是直接抓取并阅读完整网页内容
"""
import re
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from scrapling.fetchers import Fetcher


class WebScraperInput(BaseModel):
    url: str = Field(description="要抓取的网页URL")
    max_chars: int = Field(default=5000, description="返回的最大字符数，默认5000")


class WebScraperTool(BaseTool):
    """Scrapling 网页内容抓取工具 — 获取页面的完整文字内容"""

    name: str = "web_scraper"
    description: str = (
        "抓取指定网页的完整文字内容。当你从搜索结果中找到感兴趣的链接、"
        "需要查看页面详情时，用这个工具获取页面的实际文本。"
        "支持中文站点（自动识别 UTF-8/GBK 编码）。"
        "参数：url（必填），max_chars（可选，默认5000字符）"
    )
    args_schema: Type[BaseModel] = WebScraperInput

    def _run(self, url: str, max_chars: int = 5000) -> str:
        try:
            Fetcher.configure(adaptive=True)
            resp = Fetcher().get(url)

            # 智能编码检测
            try:
                html = resp.body.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                try:
                    html = resp.body.decode('gbk')
                except:
                    return f"❌ 无法解码页面: {url}"

            # 清洗：去掉 script/style/nav/footer
            text = re.sub(
                r'<(script|style|meta|noscript|iframe|nav|footer|header)[^>]*>.*?</\1>',
                '', html, flags=re.DOTALL | re.IGNORECASE
            )
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'&[a-z]{2,6};', ' ', text)

            if len(text) < 100:
                return f"⚠️ 页面内容过短（{len(text)}字符），可能是 JS 动态渲染页面，建议换其他链接"

            total = len(text)
            if total > max_chars:
                text = text[:max_chars] + f"\n\n... (已截断，完整内容共 {total:,} 字符)"

            return f"[页面内容] {url}\n\n{text}"

        except Exception as e:
            return f"❌ 抓取失败: {type(e).__name__}: {e}"


def quick_scrape(url: str, max_chars: int = 5000) -> str:
    """快速抓取，返回纯文本（非 Agent 调用用）"""
    try:
        Fetcher.configure(adaptive=True)
        resp = Fetcher().get(url)
        html = resp.body.decode('utf-8', errors='replace')
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except:
        return ""
