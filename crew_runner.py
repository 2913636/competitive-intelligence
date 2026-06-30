"""
竞品情报分析 Agent 系统 — CrewAI 编排核心

3 个 Agent 串联：
  Researcher → Analyst → Writer
  搜索公开信息 → 提取关键洞察 → 生成专业报告
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from tools.web_search import WebSearchTool
from tools.web_scraper import WebScraperTool

load_dotenv()

# ====== DeepSeek 模型配置 ======
deepseek_llm = LLM(
    model="deepseek/deepseek-chat",
    api_key=os.getenv("DEEPSEEK_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    temperature=0.3,
)

# ====== 工具工厂（每次调用创建新实例，避免并发冲突）======

def _create_agents():
    """每次分析创建全新的 Agent 实例，避免 CrewAI 并发冲突"""
    web_search_tool = WebSearchTool()
    web_scraper_tool = WebScraperTool()

    researcher = Agent(
        role="资深市场情报研究员",
        goal="搜索目标公司的公开信息，从多维度收集原始数据，每个维度都要有搜索结果",
        backstory=(
            "你有10年市场调研经验，擅长从网络公开信息中挖掘有价值的情报。"
            "你从不依赖记忆，每次都必须使用 web_search 工具去搜索最新信息。"
            "你会从公司基础信息、产品定价、用户评价、行业地位、最新动态5个维度全面搜索。"
            "搜索结果中如果有重要的链接，使用 web_scraper 工具抓取完整页面内容进行分析。"
        ),
        tools=[web_search_tool, web_scraper_tool],
        llm=deepseek_llm,
        verbose=True,
    )

    analyst = Agent(
        role="资深市场战略分析师",
        goal="从研究员收集的原始信息中提取关键洞察，识别竞争优势、劣势与市场定位",
        backstory=(
            "你曾在麦肯锡工作8年，专注于科技行业竞争分析。"
            "你善于从零散信息中看出竞争格局，从不编造数据——搜索结果里没有的，你会明确标注。"
            "你的分析框架：公司概览 → 产品分析 → 优势 → 劣势 → 市场定位 → 近期动态。"
        ),
        tools=[],
        llm=deepseek_llm,
        verbose=True,
    )

    writer = Agent(
        role="资深商业分析报告撰写人",
        goal="将分析结果写成一份专业、结构清晰、可直接交付客户的 Markdown 竞品分析报告",
        backstory=(
            "你写了15年商业分析报告，客户包括红杉、高瓴等顶级投资机构。"
            "你的报告以结构清晰、重点突出、信息可溯源著称。"
            "你使用标准 Markdown 格式，善用表格呈现关键信息，每条结论都有依据。"
        ),
        tools=[],
        llm=deepseek_llm,
        verbose=True,
    )

    return researcher, analyst, writer

# ====== 任务定义 ======

def create_research_task(company: str, researcher: Agent) -> Task:
    return Task(
        description=(
            f"搜索目标公司「{company}」的公开信息。\n\n"
            f"必须从以下 5 个维度分别搜索（每次搜索用不同的关键词）：\n"
            f"1. 公司基础信息：搜索「{company} 公司 成立 融资 团队 总部」\n"
            f"2. 产品与定价：搜索「{company} 产品 定价 功能 服务」\n"
            f"3. 用户评价：搜索「{company} 评价 优缺点 用户反馈 投诉」\n"
            f"4. 行业地位：搜索「{company} 市场份额 竞品 行业排名」\n"
            f"5. 最新动态：搜索「{company} 最新 新闻 2025 2026」\n\n"
            f"重要：必须使用 web_search 工具执行每一次搜索，不要跳过任何维度。\n"
            f"对于搜索结果中的高价值链接（公司官网、产品页面、新闻稿），"
            f"必须使用 web_scraper 工具抓取完整页面内容，获取比摘要更详细的信息。\n"
            f"把所有搜索结果整理成结构化的信息，为后续分析提供原材料。"
        ),
        expected_output=(
            f"关于「{company}」的5维度搜索结果汇总，包含：\n"
            f"- 公司基础信息（成立时间、总部、融资、团队规模）\n"
            f"- 产品与定价信息\n"
            f"- 用户评价摘要\n"
            f"- 行业地位与竞品\n"
            f"- 最新动态\n"
            f"搜索结果中缺失的信息请标注「未找到公开信息」"
        ),
        agent=researcher,
    )


def create_analysis_task(company: str, analyst: Agent) -> Task:
    return Task(
        description=(
            f"基于研究员的搜索结果，对「{company}」进行深度分析。\n\n"
            f"请按以下框架输出结构化分析（JSON 格式）：\n"
            f"1. company_overview：公司概览（名称、成立时间、总部、融资、团队）\n"
            f"2. product_analysis：产品分析（核心产品、定价策略、目标用户）\n"
            f"3. strengths：竞争优势（至少2条）\n"
            f"4. weaknesses：竞争劣势（至少2条）\n"
            f"5. market_position：市场定位（份额、主要竞品、差异化）\n"
            f"6. recent_moves：近期动态\n\n"
            f"关键原则：绝不编造数据。搜索结果里没有的信息，标注「未找到公开信息」。"
        ),
        expected_output=(
            f"关于「{company}」的结构化 SWOT 分析，JSON 格式，"
            f"每个字段基于搜索结果填写，缺失数据明确标注"
        ),
        agent=analyst,
    )


def create_report_task(company: str, writer: Agent) -> Task:
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return Task(
        description=(
            f"基于分析师的结构化分析结果，撰写「{company}」的竞品分析报告。\n\n"
            f"报告必须使用以下 Markdown 模板：\n\n"
            f"# 竞品分析报告：{company}\n\n"
            f"> 生成时间：{now} | 数据来源：公开网络搜索 | 分析工具：AI Agent 自动生成\n\n"
            f"## 一、公司概览\n"
            f"用表格呈现：成立时间 | 总部 | 融资阶段 | 团队规模\n\n"
            f"## 二、产品分析\n"
            f"核心产品、定价策略、目标用户\n\n"
            f"## 三、竞争优势\n"
            f"分点列出（每条有依据）\n\n"
            f"## 四、竞争劣势与风险\n"
            f"分点列出（每条有依据）\n\n"
            f"## 五、市场定位\n"
            f"市场份额、主要竞品、差异化能力\n\n"
            f"## 六、近期动态\n"
            f"近半年重要事件\n\n"
            f"## 七、总结与建议\n"
            f"3-5条可操作建议\n\n"
            f"---\n"
            f"*本报告由 AI Agent 系统自动生成（研究员→分析师→写手三Agent协作），"
            f"数据来源为公开网络搜索，仅供参考。*"
        ),
        expected_output=(
            f"一份完整的「{company}」竞品分析 Markdown 报告，"
            f"包含7个章节，可直接保存为 .md 文件"
        ),
        agent=writer,
    )


# ====== Crew 编排 ======

def run_analysis(company: str) -> dict:
    """
    执行竞品分析，返回报告内容和元信息

    返回:
        {
            "success": True/False,
            "company": "公司名",
            "report": "Markdown 报告内容",
            "timestamp": "时间戳",
            "error": None 或 错误信息
        }
    """
    if not company or not company.strip():
        return {
            "success": False,
            "company": company,
            "report": "",
            "timestamp": datetime.now().isoformat(),
            "error": "请输入公司或产品名称"
        }

    company = company.strip()

    # 每次调用创建全新的 Agent 实例，避免 CrewAI 并发冲突
    researcher, analyst, writer = _create_agents()

    # 创建任务
    research_task = create_research_task(company, researcher)
    analysis_task = create_analysis_task(company, analyst)
    report_task = create_report_task(company, writer)

    # 创建 Crew — 顺序执行
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True,
    )

    # 执行
    try:
        result = crew.kickoff(inputs={"company": company})
        return {
            "success": True,
            "company": company,
            "report": str(result),
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "company": company,
            "report": "",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# ====== 命令行入口 ======
if __name__ == "__main__":
    company = input("请输入要分析的公司或产品名称：")
    print(f"\n开始分析「{company}」...\n")
    result = run_analysis(company)

    if result["success"]:
        print("\n" + "=" * 60)
        print(result["report"])
        print("=" * 60)
    else:
        print(f"\n分析失败: {result['error']}")
