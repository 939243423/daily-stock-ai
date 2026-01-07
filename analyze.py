import os
import json
import datetime
import time
import requests
from google import genai
from google.genai import types

def call_gemini(client, prompt):
    """
    尝试调用 Gemini 系列模型。
    包含：
    1. 修正后的模型名称列表 (解决 404)
    2. 智能退避重试策略 (解决 429)
    """
    # 按照优先级排序的模型列表
    # gemini-2.0-flash-exp: 最新，速度快
    # gemini-1.5-flash: 最稳定，主力模型
    # gemini-1.5-flash-8b: 轻量级，备用
    models = [
        'gemini-2.0-flash-exp', 
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b'
    ]
    
    for model_name in models:
        # 每个模型允许重试 3 次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🚀 [模型: {model_name}] 第 {attempt + 1}/{max_retries} 次尝试...")
                
                # 请求前强制休眠 2 秒，平滑请求频率
                time.sleep(2)
                
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                
                if response and response.text:
                    return response.text, f"Gemini({model_name})"
            
            except Exception as e:
                error_str = str(e)
                
                # --- 场景 1: 429 限流 (最常见问题) ---
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 20 * (attempt + 1) # 第一次等20秒，第二次等40秒...
                    print(f"⏳ 触发限流 (429)，暂停 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue # 继续下一次循环重试当前模型
                
                # --- 场景 2: 404 模型未找到 ---
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    print(f"⚠️ 模型 {model_name} 名称无效或未发布，跳过...")
                    break # 跳出当前模型的重试循环，尝试下一个模型
                
                # --- 场景 3: 其他错误 (如 500, 503) ---
                else:
                    print(f"⚠️ 未知错误: {error_str[:100]}")
                    # 如果不是最后一次尝试，稍作等待
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
    # 1. 获取 Key
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    client = None
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
        except Exception as e:
            print(f"Gemini Client 初始化失败: {e}")
    
    # 2. 核心 Prompt：植入了您要求的 5 档色阶评分逻辑
    prompt = """
    你是一位专门服务于普通散户投资者的顶级 A 股策略师。
    请挑选 3 只同时满足以下【硬性门槛】和【选股逻辑】的股票。

    【硬性门槛 - 必须遵守】：
    1. 零门槛参与：仅限沪深主板个股（代码 60XXXX 或 00XXXX）。
    2. 禁止筛选：禁止推荐科创板、创业板、北交所及港股。

    【选股逻辑】：
    1. 估值洼地：处于历史估值底部、破净或低 PE 的行业龙头。
    2. 主力入场：近期成交量异常放大，底部放量，显示大资金建仓。
    3. 安全边际：基本面稳健，避开 ST 和近期暴涨妖股。

    【🔥🔥🔥 评分标准（非常重要）🔥🔥🔥】：
    请务必根据以下标准拉开分差，不要全部给出 90 分！
    
    * **90-99 分 (极高)**：完美标的。估值处于历史极低位，且主力资金近日有巨量流入，基本面无懈可击。（对应前端：梦幻紫渐变）
    * **80-89 分 (高)**：优秀标的。基本面扎实，技术面刚形成突破，确定性高。（对应前端：宝石蓝）
    * **70-79 分 (中高)**：稳健标的。长期看好，但短期爆发力可能不如前两者。（对应前端：翡翠绿）
    * **60-69 分 (中)**：观察标的。位置较低但启动迹象不明显，需要潜伏。（对应前端：活力橙）
    * **< 60 分 (低)**：风险标的。（对应前端：警示红）

    请严格以下 JSON 格式输出（不要输出 Markdown 代码块标记）：
    {
      "stocks": [
        {
          "name": "股票名称",
          "code": "代码",
          "reason": "【估值逻辑+主力迹象】详细分析...",
          "risk": "风险提示...",
          "score": 85
        }
      ]
    }
    """
    
    # 3. 执行调用
    res_text, source = None, None
    
    if client:
        res_text, source = call_gemini(client, prompt)
    
    # 降级策略
    if not res_text and deepseek_key:
        res_text, source = call_deepseek(deepseek_key, prompt)

    if not res_text:
        print("❌ 致命错误：所有 AI 均无法生成数据，请检查网络或 Key 配额。")
        return

    # 4. 数据处理
    try:
        # 清洗 Markdown 标记
        res_text = res_text.strip()
        if res_text.startswith("```"):
            lines = res_text.splitlines()
            # 去掉第一行 ```json 和最后一行 ```
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            res_text = "\n".join(lines)
        
        data = json.loads(res_text)
        
        if 'stocks' not in data:
            print("❌ 数据格式错误：缺少 'stocks' 字段")
            return

        # 5. 写入文件
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
