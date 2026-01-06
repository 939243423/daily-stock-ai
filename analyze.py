import os
import json
import datetime
import time
from google import genai

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("错误: 未找到 API KEY")
        return

    client = genai.Client(api_key=api_key)

    market_context = "当前市场：有色金属、AI算力板块活跃。请分析紫金矿业、宁德时代、中际旭创。"

    prompt = f"作为资深分析师，请从以下股票中挑3只，以JSON格式输出：{{'stocks': [{{'name': '...', 'code': '...', 'reason': '...', 'risk': '...', 'score': 95}}]}}。数据：{market_context}"

    # 优化后的模型列表
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash']
    response = None
    success_model = ""

    for model_name in models_to_try:
        try:
            print(f"正在尝试使用: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            success_model = model_name
            break 
        except Exception as e:
            print(f"模型 {model_name} 暂时无法使用: {e}")
            if "429" in str(e):
                print("检测到频率限制，等待 30 秒后尝试备选方案...")
                time.sleep(30) # 遇到 429 时多等一会儿
            continue

    if not response:
        print("❌ 所有模型均调用失败，请检查 API Key 状态或配额。")
        return

    try:
        raw_text = response.text.strip()
        # 增强型 JSON 清洗
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        recommendations = json.loads(raw_text)
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)

        all_data = {}
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    all_data = json.load(f)
                except: pass

        all_data[today] = recommendations
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 成功！使用模型: {success_model}")

    except Exception as e:
        print(f"❌ 解析失败: {e}")
        raise e

if __name__ == "__main__":
    main()
