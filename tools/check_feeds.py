import json

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])

# 查找 questions/.../feeds API
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    if '/api/v4/questions/' in url and '/feeds' in url:
        print(f"\n找到 feeds API (条目{i}): {url[:200]}")
        
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                print(f"响应数据结构:")
                print(f"  顶层键: {list(data.keys())}")
                
                if 'data' in data and isinstance(data['data'], list):
                    print(f"  data列表长度: {len(data['data'])}")
                    
                    # 检查第一个item
                    if data['data']:
                        item = data['data'][0]
                        print(f"\n  第一个item的键: {list(item.keys())[:15]}")
                        
                        # 检查target字段
                        target = item.get('target', {})
                        if isinstance(target, dict):
                            print(f"  target的键: {list(target.keys())[:25]}")
                            
                            # 检查是否包含问题或回答的内容
                            if 'question' in target:
                                question = target['question']
                                print(f"\n  包含question字段!")
                                if isinstance(question, dict):
                                    print(f"    question的键: {list(question.keys())[:15]}")
                                    print(f"    问题标题: {question.get('title', 'N/A')[:100]}")
                                    print(f"    问题ID: {question.get('id', 'N/A')}")
                            
                            if 'content' in target or 'excerpt' in target or 'detail' in target:
                                content_field = target.get('content') or target.get('excerpt') or target.get('detail', '')
                                print(f"\n  包含内容字段!")
                                print(f"    内容预览: {str(content_field)[:200]}")
                            
                            if 'type' in target:
                                print(f"  target类型: {target.get('type')}")
                                
            except Exception as e:
                print(f"解析失败: {e}")
        
        print("\n" + "="*80)

