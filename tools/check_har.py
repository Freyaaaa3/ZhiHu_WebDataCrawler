import json

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])
print(f"总条目数: {len(entries)}")

# 查找知乎 API 响应
zhihu_api_entries = []
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    if 'api.zhihu.com' in url or ('zhihu.com' in url and '/api/' in url):
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        if text:
            zhihu_api_entries.append((i, url, text[:200]))

print(f"\n找到 {len(zhihu_api_entries)} 个知乎API响应:")
for idx, (i, url, preview) in enumerate(zhihu_api_entries[:10]):
    print(f"\n{idx+1}. 条目{i}: {url[:150]}")
    print(f"   响应预览: {preview}")

# 检查一个完整的响应
if zhihu_api_entries:
    idx, url, _ = zhihu_api_entries[0]
    entry = entries[idx]
    response = entry.get('response', {})
    content = response.get('content', {})
    text = content.get('text', '')
    
    print(f"\n\n检查第一个响应的完整结构:")
    print(f"URL: {url}")
    print(f"响应文本长度: {len(text)}")
    
    # 尝试解析 JSON
    try:
        data = json.loads(text)
        print(f"JSON解析成功!")
        print(f"数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"顶层键: {list(data.keys())[:10]}")
            if 'data' in data:
                print(f"data类型: {type(data['data'])}")
                if isinstance(data['data'], list):
                    print(f"data是列表，长度: {len(data['data'])}")
                    if data['data']:
                        print(f"第一个元素键: {list(data['data'][0].keys())[:10] if isinstance(data['data'][0], dict) else 'N/A'}")
                elif isinstance(data['data'], dict):
                    print(f"data是字典，键: {list(data['data'].keys())[:10]}")
    except Exception as e:
        print(f"JSON解析失败: {e}")
        print(f"前500字符: {text[:500]}")

