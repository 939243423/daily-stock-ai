import os
import json
import datetime
import time
import requests
from google import genai

def call_gemini(client, prompt):
    """
    智能调用 Gemini：先获取可用模型列表，再匹配调用，解决 404 问题。
    """
    try:
        all_models = list(client.models.list())
        available_model_names = [m.name.split('/')[-1] for m in all_models]
        print(f"📋 你的 API Key 可用模型: {available_model_names}")
    except Exception as e:
        print(f"⚠️ 无法获取模型列表: {e}")
        available_model_names = []

    # 优先顺序：2.0 预览版(数据新) > 1.5 Pro > 1.5 Flash
    priority_list = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-1.5-flash-002'
    ]

    candidates = [m for m in priority_list if m in available_model_names]
    if not candidates:
        candidates = ['gemini-1.5-flash']

    for model_name in candidates:
        try:
            print(f"🚀 正在尝试 Gemini 模型: {model_name}...")
            time.sleep(2) 
            
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            
            if response and response.text:
                return response.text, f"Gemini({model_name})"
        
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                print(f"⏳ {model_name} 限流 (429)，尝试下一个模型...")
                time.sleep(2)
            else:
                print(f"⚠️ {model_name} 报错: {error_str[:50]}")
            continue

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
    
    # --- 核心修改：在 Prompt 中增加了 price 字段的要求 ---
    prompt = """
    你是一位专门服务于普通散户投资者的顶级 A 股策略师。
    请挑选 3 只同时满足以下【硬性门槛】和【选股逻辑】的股票。

    【硬性门槛】：
    1. 仅限沪深主板（60XXXX 或 00XXXX）。
    2. 禁止科创板、创业板、北交所、港股。

    【选股逻辑】：
    1. 估值洼地：低 PE/PB 的行业龙头。
    2. 主力入场：底部放量，大资金建仓。
    3. 安全边际：避开 ST 和妖股。

    【评分标准】：
    - 90-99 分 (极高)：梦幻紫
    - 80-89 分 (高)：宝石蓝
    - 70-79 分 (中高)：翡翠绿
    - 60-69 分 (中)：活力橙
    - < 60 分 (低)：警示红

    请严格以下 JSON 格式输出：
    {
      "stocks": [
        {
          "name": "股票名称",
          "code": "代码",
          "price": "12.34",  // ⚠️ 新增：截止昨日收盘的参考价格(数字字符串)
          "reason": "详细分析...",
          "risk": "风险提示...",
          "score": 85
        }
      ]
    }
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

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)
        
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
