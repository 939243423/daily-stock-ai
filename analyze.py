import os
import json
import datetime
import time
import requests
import yfinance as yf
from google import genai
from google.genai import types

# --- 1. 股价获取逻辑 ---
def get_real_price(code):
    """根据 A 股代码获取昨日收盘价 (yfinance)"""
    try:
        # 判断后缀 (.SS 沪市, .SZ 深市)
        ticker_symbol = ""
        if code.startswith("6") or code.startswith("9"):
            ticker_symbol = f"{code}.SS"
        elif code.startswith(("0", "2", "3")):
            ticker_symbol = f"{code}.SZ"
        else:
            return None 

        ticker = yf.Ticker(ticker_symbol)
        # 获取最近5天数据，确保能覆盖周末或节假日
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            latest_price = hist['Close'].iloc[-1]
            return f"{latest_price:.2f}"
            
    except Exception as e:
        print(f"⚠️ 无法获取 {code} 的股价: {e}")
    return None

# --- 2. Gemini 调用逻辑 ---
def call_gemini(client, prompt):
    """使用最新 SDK 调用 Gemini，支持自动降级和重试"""
    # 按照优先级排序的模型列表（使用 2.0 稳定版）
    models = [
        'gemini-2.0-flash', 
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b'
    ]
    
    for model_name in models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🚀 [模型: {model_name}] 第 {attempt + 1}/{max_retries} 次尝试...")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        # 核心优化：强制模型返回 JSON 格式，不带 Markdown 标签
                        response_mime_type='application/json',
                        temperature=0.2, # 降低随机性，使结果更稳健
                    )
                )
                
                if response and response.text:
                    return response.text, f"Gemini({model_name})"
            
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 25 * (attempt + 1)
                    print(f"⏳ 触发限流，暂停 {wait_time} 秒...")
                    time.sleep(wait_time)
                elif "404" in error_str:
                    print(f"⚠️ 模型 {model_name} 未找到，跳过...")
                    break 
                else:
                    print(f"⚠️ 错误: {error_str[:100]}")
                    time.sleep(5)
                    break
    return None, None

# --- 3. DeepSeek 备选逻辑 ---
def call_deepseek(api_key, prompt):
    print("🔄 尝试切换至 DeepSeek 备用通道...")
    url = "[https://api.deepseek.com/chat/completions](https://api.deepseek.com/chat/completions)"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位 A 股量化交易专家。请严格按 JSON 格式回答。"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()['choices'][0]['message']['content'], "DeepSeek"
    except Exception as e:
        print(f"❌ DeepSeek 调用失败: {e}")
        return None, None

# --- 4. 主程序 ---
def main():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    if not gemini_key:
        print("❌ 错误: 未设置 GEMINI_API_KEY 环境变量")
        return

    client = genai.Client(api_key=gemini_key)

    prompt = """
    挑选 3 只满足以下条件的 A 股主板股票 (60XXXX 或 00XXXX)。
    逻辑：1. 估值洼地 2. 主力底部放量 3. 避开 ST。
    
    必须严格按以下 JSON 格式输出，不要包含任何解释文字：
    {
      "stocks": [
        {
          "name": "股票名称",
          "code": "代码",
          "price": "参考股价",
          "tags": ["板块", "资金面", "基本面"],
          "reason": "推荐理由(包含估值和成交量分析)",
          "risk": "风险提示",
          "score": 85
        }
      ]
    }
    """
    
    # 1. 获取 AI 生成内容
    res_text, source = call_gemini(client, prompt)
    if not res_text and deepseek_key:
        res_text, source = call_deepseek(deepseek_key, prompt)

    if not res_text:
        print("❌ 所有 AI 服务均不可用")
        return

    # 2. 解析与校准
    try:
        data = json.loads(res_text)
        print(f"🔍 AI 推荐完毕 (来源: {source})，开始联网校准价格...")

        for stock in data.get('stocks', []):
            code = stock.get('code', '')
            if code:
                real_price = get_real_price(code)
                if real_price:
                    print(f"   ✅ {stock['name']}({code}): AI 报价 {stock.get('price')} -> 真实收盘价 {real_price}")
                    stock['price'] = real_price
                else:
                    print(f"   ⚠️ {stock['name']}({code}): 联网查价失败，保留原报价")

        # 3. 写入历史记录 (处理北京时间)
        # GitHub Actions 默认是 UTC，我们手动加 8 小时得到北京日期
        bj_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        today_str = bj_time.strftime("%Y-%m-%d")
        
        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)
        
        history_data = {}
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    history_data = json.load(f)
                except:
                    history_data = {}

        history_data[today_str] = data
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 任务完成！数据已存入 history.json (日期: {today_str})")

    except Exception as e:
        print(f"❌ 处理数据时出错: {e}")
        print(f"原始内容: {res_text}")

if __name__ == "__main__":
    main()
