import os
import json
import datetime
import google.generativeai as genai

# 配置 API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro') # 建议先用这个成熟版本，或者 gemini-exp-1206

def main():
    # 模拟获取今日热门股票数据
    market_data = "今日热门：紫金矿业(601899)放量上涨；宁德时代(300750)资金流入..."
    
    prompt = f"你是一个资深分析师。根据以下数据：{market_data}，请挑选3只最具潜力股票，以JSON格式输出：{{'date': '2026-01-05', 'stocks': [{{'name': '...', 'code': '...', 'reason': '...'}}]}}"
    
    response = model.generate_content(prompt)
    # 提取 JSON 部分
    result_text = response.text.replace('```json', '').replace('```', '').strip()
    new_data = json.loads(result_text)
    
    # 写入文件
    with open('data/history.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data[datetime.datetime.now().strftime("%Y-%m-%d")] = new_data
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
