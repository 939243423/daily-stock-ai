import os
import json
import datetime
import time
import requests
from google import genai

def call_gemini(client, prompt):
    """尝试调用 Gemini 系列模型，包含降级逻辑"""
    # 优先用 2.0-flash (平衡)，备选 1.5-flash-8b (极速且配额足)
    models = ['gemini-2.0-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-flash']
    for model_name in models:
        try:
            print(f"🚀 正在尝试 Gemini 模型: {model_name}...")
            # 增加 2 秒延迟，避免请求过快触发 429
            time.sleep(2) 
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            if response and response.text:
                return response.text, f"Gemini({model_name})"
        except Exception as e:
            print(f"⚠️ Gemini {model_name} 暂时不可用: {str(e)[:100]}")
            if "429" in str(e):
                print("⏳ 触发限流，等待 10 秒...")
                time.sleep(10)
            continue
    return None, None

def call_deepseek(api_key, prompt):
    """作为备选方案调用 DeepSeek API"""
    print("🔄 Gemini 全部失效，启动 DeepSeek 备选方案...")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # 针对选股逻辑，使用 deepseek-chat (或根据需求选 deepseek-reasoner)
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
        print(f"❌ DeepSeek 调用也失败了: {e}")
        return None, None

def main():
    # 1. 初始化环境变量
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    client = genai.Client(api_key=gemini_key) if gemini_key else None
    
    # 2. 定义高度专业的选股 Prompt
    # 融合了：低估值 + 主力异动 + 安全边际
    prompt = """
    你是一位资深基金经理，擅长挖掘“低位放量”和“估值修复”型牛股。
    请分析当前 A 股市场环境，挑选 3 只满足以下【硬性条件】的个股：
    
    条件 1：估值洼地。PE(TTM)或PB处于行业较低分位，具有较高的安全边际。
    条件 2：主力异动。近期（3-5日内）成交量明显放大，股价脱离底部平台，显示主力资金有明显的入场扫货迹象。
    条件 3：低风险特征。基本面稳健（如ROE良好、负债率合理），非ST、非次新、非近期大涨过的个股。
    
    请严格以下 JSON 格式输出，不要包含 Markdown 标签或多余文字：
    {
      "stocks": [
        {
          "name": "股票名称",
          "code": "代码",
          "reason": "【估值逻辑+主力迹象】详细分析理由",
          "risk": "当前主要的风险点",
          "score": 90
        }
      ]
    }
    """

    # 3. 执行调用逻辑
    res_text, source = None, None
    
    if client:
        res_text, source = call_gemini(client, prompt)
    
    if not res_text and deepseek_key:
        res_text, source = call_deepseek(deepseek_key, prompt)

    if not res_text:
        print("❌ 致命错误：所有 AI API 均无法访问，请检查配额或网络。")
        return

    # 4. 数据解析与持久化
    try:
        # 清洗 JSON 字符串（防止 AI 自动添加 ```json ... ```）
        res_text = res_text.strip()
        if "```" in res_text:
            res_text = res_text.split("```")[1]
            if res_text.startswith("json"):
                res_text = res_text[4:].strip()
        res_text = res_text.strip("` \n")
        
        data = json.loads(res_text)
        
        # 确保数据结构包含 stocks 键
        if 'stocks' not in data:
            print("❌ AI 输出格式不正确")
            return

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        history_path = 'data/history.json'
        
        # 确保目录存在
        os.makedirs('data', exist_ok=True)
        
        # 读取旧数据
        all_history = {}
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    all_history = json.load(f)
                except:
                    all_history = {}

        # 写入新数据
        all_history[today] = data
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_history, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 更新成功！今日推荐由 {source} 生成。")

    except Exception as e:
        print(f"❌ 解析数据或写入文件时出错: {e}")
        print(f"原始输出内容: {res_text[:500]}...")

if __name__ == "__main__":
    main()
