# 📈 AI 股市雷达 (Daily Stock AI)

[![Deploy to Cloudflare Pages](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml/badge.svg)](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![AI](https://img.shields.io/badge/AI-Gemini%20%2F%20DeepSeek-purple)

## 📖 项目介绍

**AI 股市雷达** 是一个基于 **GitHub Actions** 和 **大语言模型 (LLM)** 的全自动量化分析工具。

它每天会在 **北京时间 08:08 (A股收盘后)** 自动运行：
1.  **数据抓取**：自动联网校准 A 股实时股价。
2.  **AI 分析**：调用 **Google Gemini 3 Pro** (或 DeepSeek) 对市场进行深度扫描。
3.  **策略筛选**：基于“低估值、主力介入、基本面稳健”三大逻辑，筛选出 3 只潜力个股。
4.  **自动部署**：分析报告生成后，自动构建静态网站并推送到 **Cloudflare Pages** 进行全球分发。

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