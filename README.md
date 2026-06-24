# 竞品情报分析 Agent 系统

输入公司名 → 3 个 AI Agent 自动协作 → 5 分钟输出专业竞品分析报告。

## 架构

```
用户输入 → 研究员(联网搜索) → 分析师(提取洞察) → 写手(生成报告) → Markdown
```

## 技术栈

- **编排：** CrewAI（多 Agent 顺序协作）
- **模型：** DeepSeek V3
- **搜索：** DuckDuckGo（免费，无需 API Key）
- **界面：** Streamlit

## 快速开始

```bash
git clone https://github.com/2913636/competitive-intelligence.git
cd competitive-intelligence
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # 编辑 .env 填入 DeepSeek Key
streamlit run main.py
```

## 项目结构

```
competitive-intelligence/
├── main.py           ← Streamlit 界面
├── crew_runner.py    ← CrewAI 编排核心（3 Agent + 3 Task）
├── tools/
│   └── web_search.py ← DuckDuckGo 搜索工具
└── reports/          ← 生成的报告存档
```

## 示例

输入 `小米` → 输出 7 章节报告：公司概览 / 产品分析 / 竞争优势 / 竞争劣势 / 市场定位 / 近期动态 / 总结建议
