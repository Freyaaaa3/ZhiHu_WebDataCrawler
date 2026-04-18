import json
import re

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])
print(f"总条目数: {len(entries)}")

# 查找可能包含问题/回答数据的响应
candidates = []
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    response = entry.get('response', {})
    content = response.get('content', {})
    text = content.get('text', '')
    
    # 查找包含问题/回答相关关键词的 URL 或响应内容
    if text and len(text) > 500:  # 只检查较大的响应
        url_lower = url.lower()
        text_lower = text.lower()[:1000] if len(text) > 1000 else text.lower()
        
        # 检查 URL 或内容中是否包含相关关键词
        keywords = ['question', 'answer', 'content', 'api/v4', 'api/v5', 'zhihu.com']
        if any(kw in url_lower for kw in keywords) or any(kw in text_lower for kw in ['question', 'answer', 'content', 'title', '问题', '回答']):
            # 尝试解析 JSON
            try:
                data = json.loads(text)
                # 检查数据结构是否像问题/回答数据
                if isinstance(data, dict):
                    keys = list(data.keys())
                    # 检查是否包含常见的数据结构
                    if 'data' in keys or 'items' in keys or 'results' in keys or 'answers' in keys or 'questions' in keys:
                        candidates.append((i, url, text, data))
            except:
                pass

print(f"\n找到 {len(candidates)} 个候选响应:")
for idx, (i, url, text, data) in enumerate(candidates[:10]):
    print(f"\n{idx+1}. 条目{i}: {url[:150]}")
    print(f"   响应长度: {len(text)}")
    if isinstance(data, dict):
        print(f"   顶层键: {list(data.keys())[:10]}")
        if 'data' in data:
            data_val = data['data']
            if isinstance(data_val, list):
                print(f"   data是列表，长度: {len(data_val)}")
                if data_val and isinstance(data_val[0], dict):
                    print(f"   第一个元素键: {list(data_val[0].keys())[:10]}")
            elif isinstance(data_val, dict):
                print(f"   data是字典，键: {list(data_val.keys())[:10]}")

# 特别查找包含 question 或 answer ID 的 URL
print("\n\n查找包含 question/answer ID 的 URL:")
question_urls = []
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    # 查找包含数字ID的question或answer URL
    if re.search(r'(question|answer|p)/\d+', url, re.I):
        question_urls.append((i, url))
        if len(question_urls) <= 10:
            print(f"{len(question_urls)}. {url[:200]}")

print(f"\n总共找到 {len(question_urls)} 个包含问题/回答ID的URL")

