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

def get_market_context():
    """
    获取昨日大盘核心指数数据 (上证、深证)
    用于喂给 AI，防止它瞎编大盘走势
    """
    context_str = ""
    try:
        # 定义指数代码: 上证指数, 深证成指
        indices = {
            "上证指数": "000001.SS",
            "深证成指": "399001.SZ"
        }
        
        context_str += "【昨日大盘真实数据】\n"
        
        for name, code in indices.items():
            ticker = yf.Ticker(code)
            # 取最近 5 天数据，确保能拿到昨天和前天的（用于计算涨跌）
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                today_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = (today_close - prev_close) / prev_close * 100
                volume = hist['Volume'].iloc[-1] / 100000000 # 换算成亿
                
                symbol = "+" if change > 0 else ""
                context_str += f"- {name}: 收盘 {today_close:.2f} 点, 涨跌幅 {symbol}{change:.2f}%, 成交量 {volume:.1f} 亿手\n"
        
        context_str += "(请基于以上真实数据进行大盘情绪研判，不要编造数据)\n"
        print("✅ 成功获取大盘行情数据")
        
    except Exception as e:
        print(f"⚠️ 获取大盘数据失败: {e}")
        # 失败了就留空，不影响后面运行
        context_str = "【大盘数据获取失败，请根据一般市场逻辑模糊分析】"
        
    return context_str
def get_latest_news():
    """
    获取东方财富 7x24 小时财经快讯 (A 股纯净版)
    仅保留与 A 股、宏观政策、核心资产相关的消息，剔除噪音。
    """
    print("📰 正在抓取 A 股核心快讯...")
    news_str = "【最新 A 股核心情报】\n"
    
    # 关键词过滤器：只有包含这些词的新闻才会被 AI 看到
    # 1. 核心指数 & 交易所
    kws_core = ["A股", "沪指", "深成指", "创业板", "科创板", "北交所", "上证", "深证", "恒生", "港股", "金龙"]
    # 2. 政策 & 宏观
    kws_policy = ["央行", "证监会", "交易所", "发改委", "国务院", "降准", "降息", "LPR", "MLF", "逆回购", "印花税", "美联储", "汇率", "人民币"]
    # 3. 市场 & 资金
    kws_market = ["融资", "北向", "外资", "主力", "资金流向", "成交量", "放量", "缩量", "涨停", "跌停", "板块", "概念", "龙虎榜", "ETF", "券商", "基金"]
    # 4. 重点行业 (可按需补充)
    kws_industry = ["半导体", "新能源", "白酒", "医药", "房地产", "银行", "中字头", "人工智能", "算力", "低空经济"]
    
    # 合并关键词库
    a_share_keywords = set(kws_core + kws_policy + kws_market + kws_industry)

    try:
        # 使用 102 频道 (全球直播) 确保不漏掉宏观大事，然后手动过滤
        url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            content = resp.text
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx : end_idx+1]
                data = json.loads(json_str)
                
                count = 0
                for item in data.get('LivesList', []):
                    title = item.get('title', '')
                    digest = item.get('digest', '')
                    show_time = item.get('showTime', '') 
                    
                    full_text = f"{title} {digest}"
                    
                    # --- [过滤逻辑] ---
                    # 1. 排除垃圾广告
                    if "推荐" in title or len(digest) < 5: continue
                    
                    # 2. 必须包含 A 股相关关键词 (核心修改)
                    # 只要命中任何一个关键词，就保留
                    if not any(k in full_text for k in a_share_keywords):
                        continue
                    # ----------------
                    
                    news_str += f"- [{show_time}] {full_text[:60]}...\n"
                    
                    count += 1
                    if count >= 8: break # 只要前 8 条最相关的
            else:
                news_str += "（数据解析异常）"
        else:
            news_str += "（接口请求失败）"
            
    except Exception as e:
        print(f"⚠️ 抓取新闻出错: {e}")
        news_str += "（暂无最新消息）"
        
    return news_str
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
    # 计算日期上下文 (让 AI 知道今天是哪天，昨天是哪天)
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_time = utc_now + datetime.timedelta(hours=8)
    today_str = beijing_time.strftime("%Y年%m月%d日")
    yesterday_str = (beijing_time - datetime.timedelta(days=1)).strftime("%Y年%m月%d日")

    # === [新增] 获取大盘真实数据 ===
    market_context = get_market_context()
    news_context = get_latest_news()       # 最新的财经快讯 (软消息)

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

    # 2. 准备 Prompt (Qwen-Max 专用版：包含情绪 + 详细新闻)
    prompt = f"""
    今天是 {today_str}。
    你是一位专门服务于 A 股散户的资深量化策略师。
    请基于以下【真实市场数据】和【昨日日期：{yesterday_str}】，完成分析。
    
    === 情报源 A：大盘数据 ===
    {market_context} 

    === 情报源 B：最新核心快讯 (重点) ===
    {news_context}

    【任务一：市场大势研判 (最重要的风控环节)】
    1. 结合上述【大盘数据】和【财经快讯】，精准判断昨日市场情绪。
    1. 结合上述大盘涨跌幅数据，分析昨日市场情绪（是恐慌杀跌，还是放量上涨？）。
    2. 如果上证指数跌幅超过 1%，请在风险提示中强调“系统性风险”。
    3. ⚠️ 重点：请根据上述财经快讯，列出 3-5 条具体的【利好】或【利空】消息摘要（如：央行降准、美联储加息、某行业重大利好等）。
    4. 给出今日仓位建议。

    【任务二：个股精选】
    挑选 3 只满足以下条件的股票：
    【硬性门槛】：
    1. 仅限沪深主板个股（代码 60XXXX 或 00XXXX）。
    2. 禁止推荐科创板、创业板、北交所及港股。
    3. ⚠️【强制去重】绝对禁止推荐以下近期已出现过的股票代码：{exclusion_str}。请挖掘新的市场机会！
    4. 请从【情报源 B】中挖掘利好线索。

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
      "market": {{
        "sentiment": "恐慌 / 谨慎 / 中性 / 乐观 / 亢奋",
        "risk_level": "High", // High(高危/绿色), Medium(震荡/黄色), Low(安全/红色) - 注意A股习惯：安全/上涨用红色
        "advice": "建议空仓观望...",
        "analysis": "昨日大盘受...影响缩量下跌...",
        "news": [  // ⚠️ 新闻轮播列表
           {{ "type": "bull", "content": "利好：央行意外降准0.5个百分点，释放长期资金" }},
           {{ "type": "bear", "content": "利空：北向资金昨日净流出超100亿" }},
           {{ "type": "info", "content": "消息：半导体板块受资金追捧，成交额破千亿" }}
        ]
      }},
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
         # 💎 第一级: ChatAnywhere (GPT Free) - 强力备用
        {
            "name": "ChatAnywhere",
            "key": os.environ.get("CHATANYWHERE_KEY"), 
            "url": "https://api.chatanywhere.tech/v1",
            "model": "gpt-5" # 免费版支持 gpt-5.2, gpt-5.1, gpt-5, gpt-4o，gpt-4.1 一天 5 次；支持 deepseek-r1, deepseek-v3, deepseek-v3-2-exp 一天 30 次，支持 gpt-4o-mini，gpt-3.5-turbo，gpt-4.1-mini，gpt-4.1-nano, gpt-5-mini，gpt-5-nano 一天 200 次。
        },
         # 🚀 第二级: GitHub Models (GPT-4) - 最强主攻
        {
            "name": "GitHub Models (GPT-4)",
            "key": os.environ.get("GH_TOKEN"),
            "url": "https://models.inference.ai.azure.com",
            "model": "gpt-4o" # 务必确认您的 Token 有 GPT-5 权限，否则改回 gpt-4o
        },
         # 🎁 第三级 (A): 阿里通义千问 - 国产兜底
        {
            "name": "Alibaba Qwen",
            "key": os.environ.get("DASHSCOPE_API_KEY"),
            "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-max"
        },
        
        # 🎁 第四级 (B): DeepSeek - 国产兜底
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
            # --- [新增] 强制清洗 tags 格式 (防 Qwen 犯傻) ---
            raw_tags = stock.get('tags', [])
            if isinstance(raw_tags, str):
                # 如果 AI 返回的是 "A, B, C" 这种字符串
                # 1. 把中文逗号替换成英文逗号
                # 2. 按逗号切割
                # 3. 去除首尾空格
                stock['tags'] = [t.strip() for t in raw_tags.replace('，', ',').split(',')]
            # ----------------------------------------------
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