import os
import json
import datetime
import time
import requests # DeepSeek 通常使用 OpenAI 兼容格式，这里用 requests 或 OpenAI 库
from google import genai

def call_gemini(client, prompt):
    # 尝试顺序：Flash 8b 最容易成功，Flash 2.0 效果最好
    models = ['gemini-1.5-flash-8b', 'gemini-1.5-flash', 'gemini-2.0-flash']
    for model_name in models:
        try:
            print(f"🚀 尝试 Gemini 模型: {model_name}...")
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text, f"Gemini({model_name})"
        except Exception as e:
            print(f"⚠️ Gemini {model_name} 失败: {str(e)[:50]}")
            time.sleep(2)
    return None, None

def call_deepseek(api_key, prompt):
    print("备选方案：尝试调用 DeepSeek API...")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-chat", # 或者 deepseek-reasoner (R1)
        "messages": [
            {"role": "system", "content": "你是一位资深投顾，请严格按JSON格式回答。"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        res_json = response.json()
        return res_json['choices'][0]['message']['content'], "DeepSeek"
    except Exception as e:
        print(f"❌ DeepSeek 也失败了: {e}")
        return None, None

def main():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    client = genai.Client(api_key=gemini_key) if gemini_key else None
    
    prompt = """
    请推荐3只今日潜力A股。严格输出JSON格式：
    {"stocks": [{"name": "股票名", "code": "代码", "reason": "理由", "risk": "风险", "score": 90}]}
    """

    # 1. 先试 Gemini
    res_text, source = call_gemini(client, prompt)
    
    # 2. Gemini 不行再试 DeepSeek
    if not res_text and deepseek_key:
        res_text, source = call_deepseek(deepseek_key, prompt)

    if not res_text:
        print("❌ 所有 AI 服务均不可用。")
        return

    # 解析与保存逻辑
    try:
        # 清洗可能存在的 Markdown 标签
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(res_text)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)
        
        all_data = {}
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try: all_data = json.load(f)
                except: pass

        all_data[today] = data
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 更新成功！来源: {source}")
    except Exception as e:
        print(f"解析失败: {e}")

if __name__ == "__main__":
    main()
