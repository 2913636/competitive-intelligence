"""
竞品情报分析 Agent 系统 — Streamlit 前端

启动方式: streamlit run main.py
"""
import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from crew_runner import run_analysis

# ====== 页面配置 ======
st.set_page_config(
    page_title="竞品情报分析 Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====== 样式 ======
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        margin-bottom: 2rem;
    }
    .report-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ====== 数据目录 ======
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

HISTORY_FILE = REPORTS_DIR / "history.json"


def load_history():
    """加载报告历史"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(entry: dict):
    """保存一条报告记录"""
    history = load_history()
    history.insert(0, entry)
    # 最多保留 50 条
    if len(history) > 50:
        history = history[:50]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def save_report_file(company: str, report: str) -> str:
    """保存报告到 .md 文件"""
    safe_name = "".join(c for c in company if c.isalnum() or c in " _-").strip()[:50]
    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = REPORTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    return str(filepath)


# ====== 侧边栏 ======
with st.sidebar:
    st.markdown("### 📋 历史记录")

    history = load_history()
    if history:
        for i, item in enumerate(history[:20]):
            with st.expander(f"{item['company']} — {item['timestamp'][:16]}", expanded=False):
                if item.get("report"):
                    st.download_button(
                        f"⬇ 下载报告",
                        data=item["report"],
                        file_name=f"{item['company']}_竞品分析.md",
                        mime="text/markdown",
                        key=f"dl_{i}"
                    )
    else:
        st.caption("暂无历史记录")


# ====== 主界面 ======
st.markdown('<div class="main-header">🔍 竞品情报分析 Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">输入一个公司或产品名，3 个 AI Agent 自动协作，生成专业竞品分析报告</div>',
    unsafe_allow_html=True
)

# 输入区
col1, col2 = st.columns([4, 1])
with col1:
    company_input = st.text_input(
        "公司/产品名称",
        placeholder="例如：字节跳动、OpenAI、比亚迪、小米汽车...",
        label_visibility="collapsed",
    )
with col2:
    run_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

# ====== 执行分析 ======
if "running" not in st.session_state:
    st.session_state["running"] = False

if run_button and not st.session_state["running"]:
    company = company_input.strip() if company_input else ""
    if not company:
        st.warning("请输入公司或产品名称")
    else:
        st.session_state["running"] = True
        with st.status(f"正在分析「{company}」...", expanded=True) as status:
            # 执行
            result = run_analysis(company)

            if result["success"]:
                status.update(label=f"✅ 「{company}」分析完成！", state="complete", expanded=False)

                # 保存
                filepath = save_report_file(company, result["report"])
                save_history({
                    "company": company,
                    "report": result["report"],
                    "timestamp": result["timestamp"],
                    "filepath": filepath
                })

                # 显示报告
                st.markdown("---")
                st.markdown("### 📄 竞品分析报告")

                with st.container():
                    st.markdown(result["report"])

                # 下载按钮
                st.download_button(
                    label="⬇ 下载 Markdown 报告",
                    data=result["report"],
                    file_name=f"{company}_竞品分析报告_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    type="primary",
                )

            else:
                status.update(label=f"❌ 分析失败", state="error", expanded=True)
                st.error(f"错误信息：{result['error']}")
                st.info("💡 可能的原因：\n- 网络连接问题\n- API Key 配置异常\n- 搜索服务暂时不可用\n\n请检查后重试。")

            # 重置运行状态，允许下次分析
            st.session_state["running"] = False

# ====== 底部信息 ======
st.markdown("---")
st.caption(
    "⚡ 基于 CrewAI + DeepSeek + DuckDuckGo | "
    "3 Agent 协作（研究员→分析师→写手）| "
    "数据来源为公开网络搜索，仅供参考"
)
