import os
import json
import datetime
from google import genai

def main():
    # 1. 初始化客户端
    # 2026年最新 SDK 建议直接通过环境变量获取 Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("错误: 未在环境变量中找到 GEMINI_API_KEY")
        return

    client = genai.Client(api_key=api_key)

    # 2. 模拟/获取市场上下文（你可以根据需要接入实时 API）
    # 这里我们构造一个包含宏观和个股的上下文，让 Gemini 有发挥空间
    market_context = """
    市场环境：沪指在3100点震荡，有色金属板块因国际铜价走高表现强劲，AI算力板块受隔夜美股拉升刺激。
    热门股票池数据：
    - 紫金矿业(601899)：当前18.52元，五日均线金叉，北向资金持续流入。
    - 宁德时代(300750)：当前165.30元，电池新技术发布，机构评级买入。
    - 工业富联(601138)：当前22.15元，成交量倍增，受益于高性能计算需求。
    - 中际旭创(300308)：800G光模块订单超预期，形态处于上升通道。
    """

    # 3. 构造深度分析 Prompt
    prompt = f"""
    你是一位拥有20年经验的顶级量化投资策略师。请分析以下数据：
    {market_context}
    
    任务：
    从中精准挑选 3 只今日最具潜力（胜率最高）的股票。
    
    输出要求：
    1. 必须严格输出 JSON 格式，不要有任何 Markdown 包裹字符。
    2. JSON 结构必须包含以下字段：
       - name: 股票名称
       - code: 股票代码
       - reason: 深度推荐理由（包含技术面和逻辑面）
       - risk: 具体的风险防范点
       - score: AI 信心指数 (1-100)
    
    JSON 示例结构:
    {{
      "stocks": [
        {{"name": "...", "code": "...", "reason": "...", "risk": "...", "score": 95}}
      ]
    }}
    """

    try:
        # 4. 调用最新的 Gemini 模型
        # 'gemini-2.0-flash' 是目前 2026 年响应最快且推理准确的平衡选择
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        # 5. 解析并清洗 JSON
        raw_text = response.text.strip()
        # 过滤掉 AI 可能自带的 ```json 标签
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        
        recommendations = json.loads(raw_text)
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # 6. 持久化存储
        history_path = 'data/history.json'
        os.makedirs('data', exist_ok=True)

        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                try:
                    all_data = json.load(f)
                except:
                    all_data = {}
        else:
            all_data = {}

        # 存入当日数据
        all_data[today] = recommendations
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"✅ {today} 推荐数据已生成并保存。")

    except Exception as e:
        print(f"❌ 运行失败: {str(e)}")
        # 确保 GitHub Action 捕获到错误
        raise e

if __name__ == "__main__":
    main()
