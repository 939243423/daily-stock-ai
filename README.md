# 📈 AI 股市雷达 (Daily Stock AI)

[![Deploy to Cloudflare Pages](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml/badge.svg)](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![AI Model](https://img.shields.io/badge/Model-GPT--4o%20%7C%20Qwen%20%7C%20DeepSeek%20%7C%20Gemini-8A2BE2)

> **“让 AI 帮你看盘，打破信息差。”**

## 📖 项目介绍

**AI 股市雷达** 是一个基于 **GitHub Actions** 和 **混合专家模型 (MoE)** 架构的全自动量化分析工具。

它不仅仅是一个简单的股票推荐系统，而是一个集成了**实时新闻抓取**、**大盘情绪研判**、**主力资金分析**于一体的智能投研驾驶舱。系统每天自动运行，生成一份可视化的市场研报。

### 🔥 核心特性

* **🧠 四级火箭 (MoE 架构)**：
    * **主力**: 🇨🇳 **阿里通义千问 (Qwen-Max)** —— 懂 A 股政策，擅长捕捉“字里行间”的利好。
    * **主攻**: 🚀 **OpenAI GPT-4o** —— 逻辑推理天花板，负责深度复盘。
    * **特攻**: 🐋 **DeepSeek-V3** —— 挖掘低估值与高成长性的潜力标的。
    * **兜底**: ✨ **Google Gemini** —— 全球视角风控与备用通道。
* **📰 消息驱动交易**：
    * 集成 **东方财富 7x24 快讯** 爬虫，实时抓取“融资保证金”、“央行降准”等重磅利好。
    * AI 自动阅读新闻，并根据**“消息面 -> 板块 -> 龙头”**的逻辑链条进行选股。
* **📊 实时数据校准**：
    * 利用 `yfinance` 实时校准股价与涨跌幅，拒绝 AI“瞎编”行情。
    * 独创**“AI 信号塔”**，可视化展示当日仓位建议（1-5成仓）。
* **📱 极致 UI/UX**：
    * **灵动岛交互**：点击研报即可触发顶部的灵动岛动画。
    * **融合式仪表盘**：像彭博终端一样专业的顶部状态栏。
    * **移动端优先**：完美的响应式设计，随时随地查看。

---

## 🛠️ 如何部署 (打造您的专属雷达)

您完全可以免费 fork 本项目，并配置成您自己的私人股票分析站。

### 第一步：Fork 项目
点击右上角的 **Fork** 按钮，将本项目复制到您的 GitHub 仓库中。

### 第二步：申请 AI 模型 Key (任选其一或全部)
本项目支持多种模型自动切换，您至少需要配置其中一种：

1.  **ChatAnywhere (推荐)**: [申请免费 Key](https://chatanywhere.tech) (支持 GPT-4o/5.0)
2.  **GitHub Models**: [申请 Azure Token](https://github.com/marketplace/models) (免费使用 GPT-4o)
3.  **阿里云百炼**: [申请 Qwen-Max Key](https://bailian.console.aliyun.com/) (国产最强，新人有免费额度)
4.  **DeepSeek**: [申请 API Key](https://platform.deepseek.com/) (性价比之王)
5.  **Google AI Studio**: [申请 Gemini Key](https://aistudio.google.com/) (免费)

### 第三步：配置 GitHub Secrets
进入您 Fork 后的仓库：
1.  点击 `Settings` -> `Secrets and variables` -> `Actions`。
2.  点击 `New repository secret`。
3.  根据您申请的 Key，添加以下变量名（Name）和对应的值（Secret）：

| 变量名 (Name) | 说明 | 必填性 |
| :--- | :--- | :--- |
| `CHATANYWHERE_KEY` | ChatAnywhere 的 API Key (转发 GPT) | ⭐ 推荐 |
| `GH_TOKEN` | GitHub Models Token (微软 Azure) | 选填 |
| `DASHSCOPE_API_KEY` | 阿里云 Qwen (通义千问) Key | ⭐ 推荐 (懂A股) |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 选填 |
| `GEMINI_API_KEY` | Google Gemini API Key | 选填 |

### 第四步：启用自动运行
1.  点击仓库上方的 `Actions` 标签。
2.  如果看到警告，点击 "I understand my workflows, go ahead and enable them"。
3.  程序默认每天 **北京时间 17:00** (UTC 9:00) 自动运行。
4.  您也可以手动点击 `Daily Stock Analysis` -> `Run workflow` 立即触发一次分析。

### 第五步：查看结果
运行成功后，数据会更新在 `dist/data/history.json` 中。
* **推荐部署方式**：建议绑定 **Cloudflare Pages** 或开启 **GitHub Pages** (指向 `dist` 目录)，即可获得一个在线访问的网站。

---

## 💻 本地开发

如果您想在本地修改代码或调试：

1.  **克隆项目**
    ```bash
    git clone [https://github.com/您的用户名/daily-stock-ai.git](https://github.com/您的用户名/daily-stock-ai.git)
    cd daily-stock-ai
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量** (Mac/Linux 示例)
    ```bash
    export DASHSCOPE_API_KEY="您的阿里云Key"
    # 或者其他 Key...
    ```

4.  **运行脚本**
    ```bash
    python analyze.py
    ```

5.  **启动前端** (推荐使用 Live Server 或简单的 Python http server)
    ```bash
    python -m http.server 8000
    # 然后浏览器访问 http://localhost:8000
    ```

---

## 📂 项目结构

```text
.
├── .github/workflows/  # GitHub Actions 自动化配置
├── assets/             # 静态资源 (CSS, JS, 图片)
├── data/               # 历史数据存储 (JSON)
├── dist/               # 构建输出目录 (用于部署)
├── analyze.py          # 核心 Python 分析脚本 (后端逻辑)
├── index.html          # 前端主页面 (Vue3 + Tailwind)
└── requirements.txt    # Python 依赖列表
```
---

## 🌟 Star History (星标趋势)

[![Star History Chart](https://api.star-history.com/svg?repos=939243423/daily-stock-ai&type=Date)](https://star-history.com/#939243423/daily-stock-ai&Date)

---

## ☕ 支持作者 (Buy me a coffee)

如果这个项目帮您赚到了钱，或者为您节省了宝贵的复盘时间，欢迎请我喝杯咖啡，这将激励我持续优化 AI 模型和策略！

<div align="center">
    <img src="dist/assets/img/reward_qr.jpg" width="250" alt="微信/支付宝赞赏码">
    <p>感谢您的支持！🧡</p>
</div>

---

## ⚠️ 免责声明

本项目由 AI 自动生成分析报告，不构成任何投资建议。股市有风险，入市需谨慎。