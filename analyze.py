import os
import json
import datetime
import time
import requests
import yfinance as yf # [新增] 引入 yfinance 库
from google import genai
from google.genai import types

# [新增] 获取真实股价的辅助函数
def get_real_price(code):
    """
    根据 A 股代码获取昨日收盘价 (yfinance)
    """
    try:
        # 1. 判断后缀 (.SS 沪市, .SZ 深市)
        ticker_symbol = ""
        if code.startswith("6") or code.startswith("9"):
            ticker_symbol = f"{code}.SS"
        elif code.startswith("0") or code.startswith("2") or code.startswith("3"):
            ticker_symbol = f"{code}.SZ"
        else:
            return None 

        # 2. 获取数据 (取过去5天数据以防周末/假期)
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            # 取最近一天的收盘价
            latest_price = hist['Close'].iloc[-1]
            return f"{latest_price:.2f}"
            
    except Exception as e:
        print(f"⚠️ 无法获取 {code} 的股价: {e}")
    
    return None

def call_gemini(client, prompt):
    """
    尝试调用 Gemini 系列模型。
    包含：修正后的模型名称列表 + 智能退避重试策略
    """
    # 按照优先级排序的模型列表
    models = [
        'gemini-2.0-flash-exp', 
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b'
    ]
    
    for model_name in models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🚀 [模型: {model_name}] 第 {attempt + 1}/{max_retries} 次尝试...")
                time.sleep(2) # 请求前强制休眠 2 秒
                
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                
                if response and response.text:
                    return response.text, f"Gemini({model_name})"
            
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 20 * (attempt + 1)
                    print(f"⏳ 触发限流 (429)，暂停 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue 
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    print(f"⚠️ 模型 {model_name} 名称无效或未发布，跳过...")
                    break 
                else:
                    print(f"⚠️ 未知错误: {error_str[:100]}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    break

    return None, None

def call_deepseek(api_key, prompt):
    """DeepSeek 备选方案"""
    print("🔄 Gemini 全线繁忙，切换至 DeepSeek 备用通道...")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位精通 A 股量化交易分析的专家。请严格按 JSON 格式回答。"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 1500
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        return res_json['choices'][0]['message']['content'], "DeepSeek"
    except Exception as e:
        print(f"❌ DeepSeek 调用失败: {e}")
        return None, None

def main():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    client = None
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
        except Exception as e:
            print(f"Gemini Client 初始化失败: {e}")
    
    # ==========================================
    # [新增逻辑 1] 读取历史数据，生成排除名单 (黑名单)
    # ==========================================
    history_path = 'dist/data/history.json'
    excluded_codes = []
    
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                # 获取所有历史日期的 keys，并按日期倒序排列
                sorted_dates = sorted(old_data.keys(), reverse=True)
                # 只看最近 5 天的数据，防止股票永远被拉黑
                recent_dates = sorted_dates[:5] 
                
                for d in recent_dates:
                    stocks = old_data[d].get('stocks', [])
                    for s in stocks:
                        code = s.get('code')
                        if code:
                            excluded_codes.append(code)
        except Exception as e:
            print(f"⚠️ 读取历史记录失败，跳过去重: {e}")

    # 去重并转为字符串
    exclusion_str = ", ".join(list(set(excluded_codes))) if excluded_codes else "无"
    print(f"🚫 本次排除的近期股票: {exclusion_str}")

    # ==========================================
    # [修改逻辑 2] 更新 Prompt，加入黑名单和多样性要求
    # ==========================================
    prompt = f"""
    你是一位专门服务于普通散户投资者的顶级 A 股策略师。
    请挑选 3 只同时满足以下【硬性门槛】和【选股逻辑】的股票。

    【硬性门槛】：
    1. 仅限沪深主板个股（代码 60XXXX 或 00XXXX）。
    2. 禁止推荐科创板、创业板、北交所及港股。
    3. ⚠️【强制去重】绝对禁止推荐以下近期已出现过的股票代码：{exclusion_str}。请挖掘新的市场机会！

    【选股逻辑】：
    1. 估值洼地：处于历史估值底部、破净或低 PE 的行业龙头。
    2. 主力入场：近期成交量异常放大，底部放量，显示大资金建仓。
    3. 安全边际：基本面稳健，避开 ST 和近期暴涨妖股。

    【评分与多样性要求（重要）】：
    * 为了体现投资组合的层次感，3 只股票的【AI 信心指数】必须拉开差距，分布在不同区间。
    * ⚠️ 强制要求：
        - 1只为【极高信心】(90-99分)：确定性最高的龙头白马。
        - 1只为【高信心】(80-89分)：攻守兼备的成长股。
        - 1只为【中高信心】(70-79分)：底部启动的潜力黑马或博弈型标的。
    * 不要让 3 只股票的分数都挤在同一个评分标准区间！

    请严格以下 JSON 格式输出（确保字段完整）：
    {{
      "stocks": [
        {{
          "name": "股票名称",
          "code": "代码",
          "price": "12.34", 
          "tags": ["沪深主板", "主力抢筹", "低估值"], 
          "reason": "【估值逻辑+主力迹象】详细分析...",
          "risk": "风险提示...",
          "score": 92 
        }}
      ]
    }}
    """
    
    res_text, source = None, None
    
    if client:
        res_text, source = call_gemini(client, prompt)
    
    if not res_text and deepseek_key:
        res_text, source = call_deepseek(deepseek_key, prompt)

    if not res_text:
        print("❌ 致命错误：所有 AI 均无法生成数据。")
        return

    try:
        res_text = res_text.strip()
        if res_text.startswith("```"):
            lines = res_text.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            res_text = "\n".join(lines)
        
        data = json.loads(res_text)
        
        if 'stocks' not in data:
            print("❌ 数据格式错误：缺少 'stocks' 字段")
            return

        # [新增] 遍历股票，强制修正为真实价格
        print("🔍 正在联网校准股价...")
        for stock in data['stocks']:
            code = stock.get('code', '')
            if code:
                real_price = get_real_price(code)
                if real_price:
                    print(f"   ✅ {stock['name']} ({code}): 修正价格 {stock.get('price')} -> {real_price}")
                    stock['price'] = real_price
                else:
                    print(f"   ⚠️ {stock['name']} ({code}): 获取股价失败，保留原值")

        # [修改] 5. 写入文件：路径改为 dist/data/ 下
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 修改点 1: 路径前加上 dist/
        history_path = 'dist/data/history.json' 
        
        # 修改点 2: 创建目录也要加上 dist/
        os.makedirs('dist/data', exist_ok=True)
        
        all_history = {}
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    all_history = json.load(f)
                except:
                    all_history = {}

        all_history[today] = data
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_history, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 数据更新成功！\n📅 日期: {today}\n🤖 模型: {source}")

    except Exception as e:
        print(f"❌ 数据解析或写入失败: {e}")
        print(f"🔍 原始返回内容:\n{res_text}")

if __name__ == "__main__":
    main()
