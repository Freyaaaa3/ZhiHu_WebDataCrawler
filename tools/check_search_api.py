import json

with open('data/test.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])

# 查找搜索 API
for i, entry in enumerate(entries):
    url = entry.get('request', {}).get('url', '')
    if '/api/v4/search_v3' in url or '/api/v4/search/customize' in url:
        print(f"\n找到搜索 API (条目{i}): {url[:200]}")
        
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                print(f"响应数据结构:")
                print(f"  顶层键: {list(data.keys())[:15]}")
                
                # 检查不同的数据结构
                if 'data' in data:
                    data_val = data['data']
                    if isinstance(data_val, list):
                        print(f"  data是列表，长度: {len(data_val)}")
                        if data_val:
                            item = data_val[0]
                            print(f"  第一个item的键: {list(item.keys())[:20]}")
                            
                            # 检查是否包含问题/回答信息
                            if 'object' in item:
                                obj = item['object']
                                print(f"  object的键: {list(obj.keys())[:20] if isinstance(obj, dict) else 'N/A'}")
                                
                                if isinstance(obj, dict):
                                    if 'question' in obj:
                                        q = obj['question']
                                        print(f"    包含question字段!")
                                        print(f"      问题标题: {q.get('title', 'N/A')[:100] if isinstance(q, dict) else 'N/A'}")
                                    
                                    if 'content' in obj or 'excerpt' in obj:
                                        content_field = obj.get('content') or obj.get('excerpt', '')
                                        print(f"    包含内容字段!")
                                        print(f"      内容预览: {str(content_field)[:200]}")
                                    
                                    if 'type' in obj:
                                        print(f"    object类型: {obj.get('type')}")
                    elif isinstance(data_val, dict):
                        print(f"  data是字典，键: {list(data_val.keys())[:20]}")
                        
            except Exception as e:
                print(f"解析失败: {e}")
        
        print("\n" + "="*80)

