# 📈 AI Stock Radar (Daily Stock AI)

[![Deploy to Cloudflare Pages](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml/badge.svg)](https://github.com/939243423/daily-stock-ai/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![AI Model](https://img.shields.io/badge/Model-GPT--4o%20%7C%20Qwen%20%7C%20DeepSeek%20%7C%20Gemini-8A2BE2)

> **"Let AI analyze the markets for you and break the information gap."**

## 📖 Project Introduction

**AI Stock Radar** is a fully automated quantitative analysis tool based on **GitHub Actions** and a **Mixture of Experts (MoE)** architecture.

It is more than just a simple stock recommendation system; it is an intelligent research cockpit integrating **real-time news scraping**, **market sentiment analysis**, and **main-force capital analysis**. The system runs automatically every day to generate a visualized market research report.

## ⌛️ Operation Overview

The morning session is often filled with "bull traps." Therefore, this project provides recommendations for establishing positions or adding orders after 13:30, once the afternoon trend has become clear. This approach is not only safer but also allows for capturing late-session opportunities created by main-force capital.

### 🔥 Core Features

* **🧠 Four-Stage Rocket (MoE Architecture)**:
    * **Primary Lead**: 🚀 **OpenAI GPT-5** —— The ceiling of logical reasoning, responsible for deep reviews.
    * **Main Force**: 🇨🇳 **Alibaba Qwen-Max** —— Understands A-share policies, skilled at capturing bullish signals "between the lines."
    * **Special Ops**: 🐋 **DeepSeek-V3** —— Digs for undervalued and high-growth potential targets.
    * **Safety Net**: ✨ **Google Gemini** —— Global perspective risk control and backup channel.
* **📰 News-Driven Trading**:
    * Integrates an **Eastmoney 7x24 Flash News** crawler to capture heavyweight catalysts such as "financing margins" and "central bank RRR cuts" in real-time.
    * AI automatically reads the news and selects stocks based on the logic chain: **"News Surface $\rightarrow$ Sector $\rightarrow$ Leading Stock."**
* **📊 Real-time Data Calibration**:
    * Uses `yfinance` to calibrate stock prices and percentage changes in real-time, preventing AI "hallucinations" regarding market data.
    * Original **"Market Research Report"** providing intelligent daily position suggestions (10%-50% allocation).
* **📱 Premium UI/UX**:
    * **Dynamic Island Interaction**: Clicking the report triggers a Dynamic Island animation at the top.
    * **Fused Dashboard**: A professional top status bar reminiscent of a Bloomberg Terminal.
    * **Mobile-First**: Perfect responsive design for viewing anywhere, anytime.

---

## 🛠️ How to Deploy (Create Your Own Radar)

You can fork this project for free and configure it as your own private stock analysis station.

### Step 1: Fork the Project
Click the **Fork** button in the top right corner to copy this project to your GitHub repository.

### Step 2: Apply for AI Model Keys (Choose one or all)
This project supports automatic switching between multiple models; you need to configure at least one:

1.  **ChatAnywhere (Recommended)**: [Apply for Free Key](https://chatanywhere.tech) (Supports GPT-4o/5.0)
2.  **GitHub Models**: [Apply for Azure Token](https://github.com/marketplace/models) (Free use of GPT-4o)
3.  **Alibaba Bailian**: [Apply for Qwen-Max Key](https://bailian.console.aliyun.com/) (Strongest domestic model, free quota for newcomers)
4.  **DeepSeek**: [Apply for API Key](https://platform.deepseek.com/) (The king of cost-performance)
5.  **Google AI Studio**: [Apply for Gemini Key](https://aistudio.google.com/) (Free, but prone to 429 errors; generally unstable)

### Step 3: Configure GitHub Secrets
In your forked repository:
1.  Go to `Settings` $\rightarrow$ `Secrets and variables` $\rightarrow$ `Actions`.
2.  Click `New repository secret`.
3.  Based on the Key you applied for, add the following Variable Names (Name) and corresponding values (Secret):

| Variable Name (Name) | Description | Necessity |
| :--- | :--- | :--- |
| `CHATANYWHERE_KEY` | ChatAnywhere API Key (GPT Proxy) | ⭐ Recommended |
| `GH_TOKEN` | GitHub Models Token (Microsoft Azure) | ⭐ Recommended |
| `DASHSCOPE_API_KEY` | Alibaba Qwen Key | ⭐ Generally Recommended (Knows A-shares but may have formatting issues) |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | Optional |
| `GEMINI_API_KEY` | Google Gemini API Key | Optional |

### Step 4: Enable Automatic Execution
1.  Click the `Actions` tab at the top of the repository.
2.  If you see a warning, click "I understand my workflows, go ahead and enable them."
3.  The program runs automatically every day at **13:30 Beijing Time** (UTC +5:30) (Note: automatic execution may have a delay of about 20 minutes).
4.  You can also manually click `Daily Stock Analysis` $\rightarrow$ `Run workflow` to trigger an analysis immediately.

### Step 5: View Results
Once successfully run, data will be updated in `dist/data/history.json`.
* **Recommended Deployment**: It is suggested to bind **Cloudflare Pages** or enable **GitHub Pages** (pointing to the `dist` directory) to obtain a publicly accessible website.

---

## 💻 Local Development

If you want to modify code or debug locally:

1.  **Clone Project**
    ```bash
    git clone [https://github.com/YourUsername/daily-stock-ai.git](https://github.com/YourUsername/daily-stock-ai.git)
    cd daily-stock-ai
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables** (Mac/Linux Example)
    ```bash
    export DASHSCOPE_API_KEY="YourAlibabaKey"
    # Or other Keys...
    ```

4.  **Run Script**
    ```bash
    python analyze.py
    ```

5.  **Start Frontend** (Recommended to use Live Server or a simple Python http server)
    ```bash
    python -m http.server 8000
    # Then visit http://localhost:8000 in your browser
    ```

---

## 📂 Project Structure

```text
.
├── .github/workflows/  # GitHub Actions automation config
├── assets/             # Static resources (CSS, JS, Images)
├── data/               # Historical data storage (JSON)
├── dist/               # Build output directory (for deployment)
├── analyze.py          # Core Python analysis script (Backend logic)
├── index.html          # Frontend main page (Vue3 + Tailwind)
└── requirements.txt    # Python dependency list
```
---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=939243423/daily-stock-ai&type=Date)](https://star-history.com/#939243423/daily-stock-ai&Date)

---

## ☕ Support the Author (Buy me a coffee)

If this project has helped you make money or saved you valuable research time, feel free to buy me a coffee! This will motivate me to continue optimizing AI models and strategies.

<div align="center">
    <img src="dist/assets/img/reward_qr.jpg" width="250" alt="WeChat/Alipay Reward QR Code">
    <p>Thank you for your support! 🧡</p>
</div>

---

## ⚠️ Disclaimer

Analysis reports in this project are automatically generated by AI and do not constitute any investment advice. Stock markets involve risk; please invest cautiously.
