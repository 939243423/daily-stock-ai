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

    market_context = """
    市场环境：沪指在3100点震荡，有色金属表现强劲，AI算力受美股刺激。
    热门股票池：紫金矿业(601899)、宁德时代(300750)、工业富联(601138)、中际旭创(300308)。
    """

    prompt = f"你是一位资深投资策略师。请分析数据并挑选3只潜力股，严格以JSON格式输出：{{'stocks': [{{'name': '...', 'code': '...', 'reason': '...', 'risk': '...', 'score': 95}}]}}。数据内容：{market_context}"

    # --- 核心降级逻辑开始 ---
    models_to_try = ['gemini-3-pro', 'gemini-2.0-flash']
    response = None
    success_model = ""

    for model_name in models_to_try:
        try:
            print(f"尝试使用模型: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            success_model = model_name
            break # 如果成功，跳出循环
        except Exception as e:
            print(f"模型 {model_name} 调用失败: {e}")
            if model_name == models_to_try[-1]: # 如果是最后一个模型也失败了
                raise e
            print("正在尝试备选模型...")
            time.sleep(2) # 稍作停顿再重试
    # --- 核心降级逻辑结束 ---

    try:
        raw_text = response.text.strip()
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        
        recommendations = json.loads(raw_text)
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)

        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    all_data = json.load(f)
                except: all_data = {}
        else:
            all_data = {}

        all_data[today] = recommendations
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 成功通过 {success_model} 生成 {today} 的推荐数据。")

    except Exception as e:
        print(f"❌ 解析数据失败: {e}")
        raise e

if __name__ == "__main__":
    main()
