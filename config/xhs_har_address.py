import json
import base64
from typing import Dict, List, Union, Any, Optional
import os
import sys
from datetime import datetime


class HarExtractor:
    def __init__(self, har_file: str):
        """
        初始化 HAR 提取器
        Args:
            har_file (str): HAR 文件的路径
        """
        self.har_file = har_file
        self.content_list = []
        print(f"\n初始化 HAR 提取器... 目标文件: {har_file}")

    def decode_base64_content(self, content: str) -> str:
        """
        解码 base64 编码的内容
        Args:
            content (str): base64 编码的字符串
        Returns:
            str: 解码后的字符串
        """
        try:
            # 添加填充
            padding = 4 - (len(content) % 4)
            if padding != 4:
                content += '=' * padding
            
            decoded = base64.b64decode(content)
            return decoded.decode('utf-8')
        except Exception as e:
            print(f"Base64 解码失败: {str(e)}")
            return content

    def extract_note_cards(self, content: Any) -> List[Dict]:
        """
        从内容中提取 note_card 信息
        Args:
            content: 解析后的内容
        Returns:
            List[Dict]: note_card 列表
        """
        note_cards = []
        try:
            if isinstance(content, dict):
                # 处理标准响应格式
                items = content.get('data', {}).get('items', [])
                for item in items:
                    if item.get('model_type') == 'note' and 'note_card' in item:
                        note_cards.append(item['note_card'])
        except Exception as e:
            print(f"提取 note_card 时发生错误: {str(e)}")
        return note_cards

    def process_content(self, content_text: str, url: str) -> Any:
        """
        处理内容文本，尝试解析 JSON 或解码 base64，并提取 note_card
        Args:
            content_text (str): 原始内容文本
            url (str): 请求URL，用于日志
        Returns:
            Any: 处理后的内容
        """
        try:
            # 首先尝试直接解析 JSON
            parsed_content = json.loads(content_text)
        except json.JSONDecodeError:
            try:
                # 如果失败，尝试解码 base64
                decoded_content = self.decode_base64_content(content_text)
                parsed_content = json.loads(decoded_content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"警告: URL {url} 的内容既不是有效的 JSON 也不是有效的 base64，将跳过")
                return None
        
        # 提取 note_cards
        return self.extract_note_cards(parsed_content)

    def extract_content(self) -> List[Dict[str, Any]]:
        """
        提取 HAR 文件中的内容，支持两种格式
        Returns:
            List[Dict]: 提取的内容列表
        """
        print("\n开始提取内容...")
        har_data = self.read_har_file()
        
        try:
            entries = har_data.get('log', {}).get('entries', [])
            total_entries = len(entries)
            print(f"找到 {total_entries} 个请求记录")
            
            for entry in entries:
                response = entry.get('response', {})
                content = response.get('content', {})
                request = entry.get('request', {})
                
                # 处理第一种格式：直接包含内容的情况
                if isinstance(entry, dict) and 'url' in entry and 'content' in entry:
                    note_cards = self.extract_note_cards(entry['content'])
                    if note_cards:
                        self.content_list.extend(note_cards)
                        print(f"成功提取 URL: {entry['url']} 的 {len(note_cards)} 个笔记")
                    continue
                
                # 处理第二种格式：标准 HAR 格式
                if content and 'text' in content:
                    url = request.get('url', '')
                    method = request.get('method', '')
                    mime_type = content.get('mimeType', '')
                    
                    # 处理内容
                    content_text = content['text']
                    note_cards = self.process_content(content_text, url)
                    
                    if note_cards:
                        self.content_list.extend(note_cards)
                        print(f"成功提取 URL: {url} 的 {len(note_cards)} 个笔记")
            
            print(f"\n内容提取完成！共提取了 {len(self.content_list)} 个内容项")
            return self.content_list
        
        except Exception as e:
            raise Exception(f"提取内容失败: {str(e)}")

    def read_har_file(self) -> Dict:
        """
        读取 HAR 文件
        Returns:
            Dict: HAR 文件的 JSON 内容
        """
        print("正在读取 HAR 文件...")
        try:
            with open(self.har_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("HAR 文件读取成功！")
                return data
        except json.JSONDecodeError as e:
            raise Exception(f"HAR 文件格式错误，不是有效的 JSON 格式: {str(e)}")
        except Exception as e:
            raise Exception(f"读取 HAR 文件失败: {str(e)}")

    def save_to_json(self, output_file: str = None) -> str:
        """
        将提取的内容保存为 JSON 文件
        Args:
            output_file (str, optional): 输出文件路径。默认为 None，将自动生成
        Returns:
            str: 保存的文件路径
        """
        if not self.content_list:
            raise Exception("没有要保存的内容，请先调用 extract_content()")
        
        if output_file is None:
            file_name = os.path.basename(self.har_file)
            base_name = os.path.splitext(file_name)[0]
            output_file = os.path.join(os.getcwd(), f"{base_name}_content.json")
        
        print(f"\n正在保存内容到文件: {output_file}")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.content_list, f, ensure_ascii=False, indent=2)
            print("文件保存成功！")
            return output_file
        except Exception as e:
            raise Exception(f"保存 JSON 文件失败: {str(e)}")

def process_har_file(har_file: str, output_file: str = None) -> Dict[str, Any]:
    """
    处理 HAR 文件的便捷函数
    Args:
        har_file (str): HAR 文件路径
        output_file (str, optional): 输出文件路径
    Returns:
        Dict: 处理结果
    """
    start_time = datetime.now()
    try:
        extractor = HarExtractor(har_file)
        content_list = extractor.extract_content()
        output_path = extractor.save_to_json(output_file)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'success': True,
            'message': f'成功提取 {len(content_list)} 个内容项',
            'output_file': output_path,
            'content_count': len(content_list),
            'processing_time': processing_time
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'output_file': None,
            'content_count': 0
        }

def main():
    """主函数，处理用户输入"""
    print("\n=== HAR 文件内容提取工具 ===")
    
    # 获取 HAR 文件路径
    while True:
        har_path = input("\n请输入HAR文件路径: ").strip()
        if not har_path:
            print("错误：文件路径不能为空")
            continue
        if not os.path.exists(har_path):
            print("错误：文件不存在")
            continue
        if not har_path.lower().endswith('.har'):
            print("错误：文件必须是 .har 格式")
            continue
        break
    
    # 获取输出路径（可选）
    output_path = input("\n请输入输出文件路径（直接回车使用默认路径）: ").strip()
    if not output_path:
        output_path = None
        print("使用默认输出路径")
    elif not output_path.lower().endswith('.json'):
        output_path = output_path + '.json'
        print(f"输出文件将保存为: {output_path}")
    
    # 处理文件
    print("\n开始处理...")
    result = process_har_file(har_path, output_path)
    
    # 打印结果
    print("\n=== 处理结果 ===")
    if result['success']:
        print(f"状态: 成功")
        print(f"输出文件: {result['output_file']}")
        print(f"提取内容数: {result['content_count']}")
        if 'processing_time' in result:
            print(f"处理时间: {result['processing_time']:.2f} 秒")
    else:
        print(f"状态: 失败")
        print(f"错误信息: {result['message']}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序发生错误: {str(e)}")
        sys.exit(1)
    finally:
        print("\n程序结束")