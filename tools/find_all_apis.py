import json
import re

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])
print(f"总条目数: {len(entries)}")

# 查找所有可能包含问题/回答数据的 API
candidates = []
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    response = entry.get('response', {})
    content = response.get('content', {})
    text = content.get('text', '')
    
    if not text or len(text) < 500:
        continue
    
    url_lower = url.lower()
    
    # 查找可能包含问题/回答数据的 URL 模式
    patterns = [
        r'/api/v\d+/questions/',
        r'/api/v\d+/answers/',
        r'/api/v\d+/search',
        r'zhihu\.com.*question',
        r'zhihu\.com.*answer',
    ]
    
    matched = False
    for pattern in patterns:
        if re.search(pattern, url_lower):
            matched = True
            break
    
    if matched:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # 检查是否包含问题/回答相关的数据结构
                has_data = 'data' in data
                has_items = 'items' in data or (isinstance(data.get('data'), list) and len(data.get('data', [])) > 0)
                
                if has_data and has_items:
                    candidates.append((i, url, len(text)))
        except:
            pass

print(f"\n找到 {len(candidates)} 个可能包含问题/回答数据的 API:")
for idx, (i, url, size) in enumerate(candidates[:30]):
    print(f"{idx+1}. 条目{i}: {url[:200]} (响应大小: {size})")

# 特别检查搜索 API
print("\n\n查找搜索相关的 API:")
search_apis = []
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    if 'search' in url.lower() and 'zhihu' in url.lower():
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        if text and len(text) > 1000:
            search_apis.append((i, url, len(text)))
            if len(search_apis) <= 10:
                print(f"{len(search_apis)}. {url[:200]} (响应大小: {len(text)})")

print(f"\n总共找到 {len(search_apis)} 个搜索 API")

