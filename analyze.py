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
        'gemini-2.0-flash-exp',           # 最新极速版 (抢手，易限流)
        'gemini-2.0-flash-thinking-exp-1219', # 思考推理版 (强力推荐)
        'gemini-1.5-pro',                 # 1.5 旗舰版 (稳定，逻辑强)
        'gemini-1.5-flash',               # 1.5 极速版
        'gemini-1.0-pro'                  # 1.0 经典版 (最后保底)
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

# --- 3. 通用 OpenAI 兼容调用函数 (Level 1-3 主力) ---
def call_openai_compatible(api_key, base_url, model_name, prompt, source_display_name):
    """
    万能接口：支持 GitHub Models, ChatAnywhere, 阿里 Qwen, DeepSeek 等
    """
    if not api_key: return None, None

    print(f"🔄 [{source_display_name}] 正在调用 {model_name} ...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是一位拥有20年经验的A股量化策略师，擅长挖掘低估值和主力资金流向。请严格遵守JSON格式输出。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "max_tokens": 1500
    }

    try:
        # ChatAnywhere 或者是 GitHub Models 有时响应较慢，设置 60秒 超时
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ [{source_display_name}] 失败: {response.status_code} - {str(response.text)[:100]}")
            return None, None
            
        res_json = response.json()
        if 'choices' in res_json and len(res_json['choices']) > 0:
            content = res_json['choices'][0]['message']['content']
            return content, f"{source_display_name}"
        else:
            print(f"❌ [{source_display_name}] 返回为空或格式异常")
            return None, None
        
    except Exception as e:
        print(f"❌ [{source_display_name}] 出错: {e}")
        return None, None

# --- 主程序 ---
def main():
    # 1. 生成排除名单
    history_path = 'dist/data/history.json'
    excluded_items = []
    excluded_codes_only = []
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                for d in sorted(old_data.keys(), reverse=True)[:10]:
                    for s in old_data[d].get('stocks', []):
                        if s.get('code'):
                            excluded_items.append(f"{s.get('name')}({s.get('code')})")
                            excluded_codes_only.append(s.get('code'))
        except: pass
    
    exclusion_str = ", ".join(list(set(excluded_items))) if excluded_items else "无"
    print(f"🚫 排除黑名单: {exclusion_str}")

    # 2. 准备 Prompt
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
          "price": "12.34",  // ⚠️ 必填：截止昨日收盘的参考价格(字符串)
          "tags": ["沪深主板", "主力抢筹", "低估值"], // ⚠️ 必填：3个简短标签，顺序代表：[1.板块, 2.资金面, 3.基本面]
          "reason": "【估值逻辑+主力迹象】详细分析...",
          "risk": "风险提示...",
          "score": 92 
        }}
      ]
    }}
    """

    # 3. === 调整后的开火顺序 ===
    # 这里的顺序严格对应您的要求
    providers = [
        # 🚀 第一级: GitHub Models (GPT-5) - 最强主攻
        {
            "name": "GitHub Models (GPT-5)",
            "key": os.environ.get("GH_TOKEN"),
            "url": "https://models.inference.ai.azure.com",
            "model": "gpt-4o" # 务必确认您的 Token 有 GPT-5 权限，否则改回 gpt-4o
        },
         # 🎁 第二级 (A): 阿里通义千问 - 国产兜底
        {
            "name": "Alibaba Qwen",
            "key": os.environ.get("DASHSCOPE_API_KEY"),
            "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-max"
        },
        # 💎 第三级: ChatAnywhere (GPT Free) - 强力备用
        {
            "name": "ChatAnywhere",
            "key": os.environ.get("CHATANYWHERE_KEY"), 
            "url": "https://api.chatanywhere.tech/v1",
            "model": "gpt-3.5-turbo" # 或者是 gpt-4，视您领取的 Key 额度而定
        },
       
        # 🎁 第三级 (B): DeepSeek - 国产兜底
        {
            "name": "DeepSeek",
            "key": os.environ.get("DEEPSEEK_API_KEY"),
            "url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        }
    ]

    final_res = None
    final_source = None

    # --- 开始逐级发射 ---
    
    # 1. 尝试 Level 1 - 3 (OpenAI 兼容通道)
    for p in providers:
        if p["key"]:
            final_res, final_source = call_openai_compatible(
                p["key"], p["url"], p["model"], prompt, p["name"]
            )
            if final_res: 
                print(f"🎉 {p['name']} 调用成功！停止后续尝试。")
                break # 成功就跳出循环，不再调用后面的
        else:
            print(f"⏭️ {p['name']} 未配置 Key，跳过...")

    # 2. 🛡️ 第四级: Gemini (最后兜底)
    # 如果前面所有通道都挂了 (final_res 还是 None)，才启动 Gemini
    if not final_res:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            print("⚠️ 前序通道全部失败，启动 Gemini 殿后...")
            try:
                client = genai.Client(api_key=gemini_key)
                final_res, final_source = call_gemini(client, prompt)
            except Exception as e:
                print(f"⚠️ Gemini 初始化失败: {e}")
        else:
            print("⏭️ Gemini 未配置 Key，无法兜底。")

    # 4. 结果处理
    if not final_res:
        print("❌ 致命错误：所有 4 级通道全部失败！请检查 API Key 或网络。")
        return

    try:
        # 清洗数据
        text = final_res.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            text = "\n".join(lines)
        
        data = json.loads(text)
        
        # 校准股价 & 写入文件
        print("🔍 正在联网校准股价...")
        valid_stocks = []
        for stock in data.get('stocks', []):
            code = stock.get('code', '')
            if code in excluded_codes_only:
                print(f"⚠️ 剔除重复推荐: {stock['name']}")
                continue
            if code:
                real_price = get_real_price(code)
                if real_price: stock['price'] = real_price
            valid_stocks.append(stock)
        
        data['stocks'] = valid_stocks
        if not data['stocks']:
            print("❌ 有效股票为0")
            return

        # 强制北京时间
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        today = (utc_now + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        
        os.makedirs('dist/data', exist_ok=True)
        path = 'dist/data/history.json'
        all_hist = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try: all_hist = json.load(f)
                except: pass
        
        all_hist[today] = data
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(all_hist, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 成功！来源: {final_source}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")

if __name__ == "__main__":
    main()