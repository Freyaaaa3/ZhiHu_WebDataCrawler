"""从 HAR 文件中提取知乎帖子及回复，保存为 Excel

使用说明（学术用途）：
1. 用抓包软件导出包含知乎请求的 HAR 文件，例如：zhihu_data.har
2. 将 HAR 文件放到本项目根目录
3. 在终端运行：
   python har_address
   或者（如果你将本文件改名为 har_address.py）：
   python har_address.py
4. 程序会输出 zhihu_har_results.xlsx
"""

import json
import os
import re
from typing import Dict, List

import pandas as pd


def html_to_text(html: str) -> str:
    """简单把 HTML 转成纯文本（去掉标签）"""
    if not isinstance(html, str):
        return ""
    # 去掉 HTML 标签
    text = re.sub(r"<[^>]+>", "", html)
    # 替换多余空白
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_har_file(har_path: str) -> Dict[str, Dict]:
    """
    解析 HAR 文件，从知乎的多个 API 接口中提取数据：
    1. /api/v4/questions/{id}/feeds - 问题feeds接口
    2. /api/v4/search_v3 - 搜索接口
    
    返回结构：
    {
        question_id_str: {
            "question_title": str,
            "question_url": str,
            "answers": [str, str, ...]  # 每个元素是一条回答的纯文本
        },
        ...
    }
    """
    with open(har_path, "r", encoding="utf-8") as f:
        har_data = json.load(f)

    entries = har_data.get("log", {}).get("entries", [])
    questions: Dict[str, Dict[str, List[str]]] = {}
    
    print(f"开始解析 {len(entries)} 个请求条目...")
    
    feeds_count = 0
    search_count = 0
    processed_count = 0

    for entry in entries:
        try:
            request = entry.get("request", {})
            response = entry.get("response", {})
            url = request.get("url", "")

            # 只处理知乎的 API
            if "zhihu.com" not in url or "/api/" not in url:
                continue

            content = response.get("content", {})
            text = content.get("text")

            if not text or len(text) < 100:
                continue

            # 解析 JSON
            try:
                data = json.loads(text)
            except Exception as e:
                # 有些工具会对 text 做 base64/压缩编码，这里暂不处理
                continue

            if not isinstance(data, dict):
                continue

            items = data.get("data")
            if not isinstance(items, list):
                continue

            # 处理 feeds API: /api/v4/questions/{id}/feeds
            if "/api/v4/questions/" in url and "/feeds" in url:
                feeds_count += 1
                
                # 解析 feeds API 的数据结构：
                # data 是一个列表，每个 item 有 target 字段
                # target 包含 question 对象和 content 字段（回答内容）
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    # 获取 target 字段
                    target = item.get("target", {})
                    if not isinstance(target, dict):
                        continue
                    
                    # 检查 target 类型，只处理 answer 类型
                    target_type = target.get("type", "")
                    if target_type != "answer":
                        continue
                    
                    # 从 target 中获取 question 信息
                    question = target.get("question", {})
                    if not isinstance(question, dict):
                        continue
                    
                    q_id = question.get("id")
                    q_title = question.get("title", "")

                    # 回答内容是 HTML，在 target.content 中
                    answer_html = target.get("content", "") or target.get("excerpt", "")
                    answer_text = html_to_text(answer_html)

                    if not q_id:
                        continue

                    q_id_str = str(q_id)

                    # 构造问题链接
                    question_url = question.get("url", "") or f"https://www.zhihu.com/question/{q_id_str}"

                    if q_id_str not in questions:
                        questions[q_id_str] = {
                            "question_title": q_title,
                            "question_url": question_url,
                            "answers": [],
                        }

                    if answer_text:
                        questions[q_id_str]["answers"].append(answer_text)
                        processed_count += 1
            
            # 处理搜索 API: /api/v4/search_v3
            elif "/api/v4/search_v3" in url:
                search_count += 1
                # 搜索 API 的数据结构：
                # data 是一个列表，每个 item 有 object 字段
                # object 包含 question 对象和 content 字段（回答内容）
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    # 获取 object 字段
                    obj = item.get("object", {})
                    if not isinstance(obj, dict):
                        continue
                    
                    # 检查 object 类型，只处理 answer 类型
                    obj_type = obj.get("type", "")
                    if obj_type != "answer":
                        continue
                    
                    # 从 object 中获取 question 信息
                    question = obj.get("question", {})
                    if not isinstance(question, dict):
                        continue
                    
                    q_id = question.get("id")
                    # 在搜索 API 中，标题可能在 object.title 而不是 question.title
                    q_title = obj.get("title", "") or question.get("title", "") or question.get("name", "")

                    # 回答内容是 HTML，在 object.content 或 object.excerpt 中
                    answer_html = obj.get("content", "") or obj.get("excerpt", "")
                    answer_text = html_to_text(answer_html)

                    if not q_id:
                        continue

                    q_id_str = str(q_id)

                    # 构造问题链接
                    question_url = obj.get("url", "") or question.get("url", "") or f"https://www.zhihu.com/question/{q_id_str}"

                    if q_id_str not in questions:
                        questions[q_id_str] = {
                            "question_title": q_title,
                            "question_url": question_url,
                            "answers": [],
                        }

                    if answer_text:
                        questions[q_id_str]["answers"].append(answer_text)
                        processed_count += 1

        except Exception as e:
            # 为了健壮性，单条 entry 出错时忽略
            continue

    print(f"解析统计:")
    print(f"  - Feeds API 请求数: {feeds_count}")
    print(f"  - 搜索 API 请求数: {search_count}")
    print(f"  - 处理的总回答数: {processed_count}")
    print(f"  - 找到的问题数: {len(questions)}")
    
    # 统计每个问题的回答数
    for q_id, info in questions.items():
        answer_count = len(info.get("answers", []))
        if answer_count > 0:
            print(f"    问题 {q_id} ({info.get('question_title', '')[:50]}): {answer_count} 条回答")
    
    return questions


def save_to_excel(questions: Dict[str, Dict], out_path: str) -> None:
    """把问题及对应的全部回答写入 Excel，一行一个问题，回答分布在不同列"""
    if not questions:
        print("未从 HAR 中解析到任何问题/回答数据。")
        return

    # 找出最大回答数量，用于确定列数
    max_answers = 0
    for q in questions.values():
        max_answers = max(max_answers, len(q.get("answers", [])))

    rows = []
    for q_id, info in questions.items():
        row = {
            "帖子内容": info.get("question_title", ""),
            "帖子链接": info.get("question_url", ""),
        }

        answers = info.get("answers", [])
        for i in range(max_answers):
            col_name = f"回复{i + 1}"
            row[col_name] = answers[i] if i < len(answers) else ""

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_excel(out_path, index=False)
    print(f"已保存到 Excel：{out_path}（共 {len(rows)} 条帖子）")


def main():
    # 默认文件名，可按需修改
    default_har = "data/test.har"
    har_path = input(f"请输入 HAR 文件路径（回车默认 {default_har}）：").strip()
    if not har_path:
        har_path = default_har

    if not os.path.exists(har_path):
        print(f"HAR 文件不存在：{har_path}")
        return

    print(f"正在解析 HAR 文件：{har_path}")
    questions = parse_har_file(har_path)

    out_path = "data/zhihu_har_results.xlsx"
    save_to_excel(questions, out_path)


if __name__ == "__main__":
    main()


