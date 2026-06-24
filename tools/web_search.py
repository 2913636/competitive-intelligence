"""
DuckDuckGo 搜索工具 — 适配 CrewAI BaseTool
"""
from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS


class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")


class WebSearchTool(BaseTool):
    """DuckDuckGo 联网搜索工具"""

    name: str = "web_search"
    description: str = "搜索互联网公开信息。输入搜索关键词，返回前5条结果的标题、摘要和链接。"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        """执行搜索，返回格式化的搜索结果"""
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    if body:
                        results.append(f"【{title}】\n{body}\n链接: {href}")

            if not results:
                return f"搜索「{query}」未找到相关结果。"

            return f"搜索关键词: {query}\n\n" + "\n\n---\n\n".join(results)

        except Exception as e:
            return f"搜索失败: {str(e)}"


def quick_search(query: str, max_results: int = 5) -> str:
    """快速搜索（非 Agent 调用时使用）"""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")
                if body:
                    results.append({
                        "title": title,
                        "body": body,
                        "href": href
                    })
        return results
    except Exception as e:
        return []
