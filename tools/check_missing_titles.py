import json

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])

# 查找搜索 API 中 question 对象的结构
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    if '/api/v4/search_v3' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                items = data.get('data', [])
                
                for item in items[:3]:  # 只检查前3个
                    obj = item.get('object', {})
                    if isinstance(obj, dict) and obj.get('type') == 'answer':
                        question = obj.get('question', {})
                        print(f"\n搜索 API 中的 question 对象:")
                        print(f"  问题ID: {question.get('id', 'N/A')}")
                        print(f"  问题标题: {question.get('title', 'N/A')}")
                        print(f"  question的所有键: {list(question.keys())[:20]}")
                        
                        # 检查是否有其他字段包含标题信息
                        if not question.get('title'):
                            print(f"  警告: 问题 {question.get('id')} 没有标题字段")
                            # 检查 object 本身是否有标题相关字段
                            print(f"  object的其他键: {[k for k in obj.keys() if 'title' in k.lower() or 'name' in k.lower()]}")
            except Exception as e:
                print(f"解析失败: {e}")
                break

