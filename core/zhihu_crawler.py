"""
知乎检索词爬虫
用于学术研究目的，爬取知乎特定检索词的帖子和用户评论
"""

import time
import random
import pandas as pd
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZhihuCrawler:
    def __init__(self, headless=False, cookie_file='zhihu_cookies.json'):
        """
        初始化爬虫
        :param headless: 是否使用无头模式
        :param cookie_file: Cookie保存文件路径
        """
        self.driver = None
        self.headless = headless
        self.results = []
        self.cookie_file = cookie_file
        
    def init_driver(self):
        """初始化Chrome浏览器驱动"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            logger.info("浏览器驱动初始化成功")
        except Exception as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            raise
    
    def save_cookies(self):
        """保存Cookie到文件"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info(f"Cookie已保存到 {self.cookie_file}")
            return True
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
            return False
    
    def load_cookies(self):
        """从文件加载Cookie"""
        try:
            if not os.path.exists(self.cookie_file):
                logger.info("Cookie文件不存在，需要重新登录")
                return False
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # 先访问知乎主页
            self.driver.get("https://www.zhihu.com")
            self.random_delay(2, 3)
            
            # 删除旧cookie并添加新cookie
            self.driver.delete_all_cookies()
            for cookie in cookies:
                try:
                    # 移除可能导致问题的字段
                    cookie.pop('sameSite', None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"添加Cookie时出错: {e}")
                    continue
            
            # 刷新页面验证登录状态
            self.driver.refresh()
            self.random_delay(2, 3)
            
            logger.info("Cookie已加载")
            return True
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return False
    
    def check_login_status(self):
        """检查是否已登录"""
        try:
            # 检查页面中是否存在登录相关的元素
            current_url = self.driver.current_url
            
            # 如果URL包含登录页面，说明未登录
            if 'signin' in current_url.lower() or 'login' in current_url.lower():
                return False
            
            # 尝试查找登录按钮或登录容器（如果存在说明未登录）
            try:
                login_selectors = [
                    "a[href*='signin']",
                    "button[class*='signin']",
                    ".SignContainer",
                    ".Login-content"
                ]
                for selector in login_selectors:
                    try:
                        login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if login_btn.is_displayed():
                            return False
                    except:
                        continue
            except:
                pass
            
            # 尝试查找用户头像或用户名（如果存在说明已登录）
            try:
                user_selectors = [
                    ".AppHeader-userInfo",
                    ".AppHeader-profile",
                    "[data-za-detail-view-element_name='UserAvatar']",
                    ".AppHeader-actions .AppHeader-userInfo",
                    "a[href*='/people/']"
                ]
                for selector in user_selectors:
                    try:
                        user_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if user_elements:
                            # 检查元素是否可见
                            for elem in user_elements:
                                if elem.is_displayed():
                                    return True
                    except:
                        continue
            except:
                pass
            
            # 检查是否有"写回答"等需要登录的功能按钮
            try:
                answer_selectors = [
                    "a[href*='/write']",
                    "button[class*='Write']",
                    ".AppHeader-actions .Button--primary"
                ]
                for selector in answer_selectors:
                    try:
                        answer_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if answer_btn.is_displayed():
                            return True
                    except:
                        continue
            except:
                pass
            
            # 检查页面标题或内容，判断是否在登录页面
            try:
                page_text = self.driver.page_source.lower()
                if '登录' in page_text and ('扫码' in page_text or 'signin' in page_text):
                    # 如果页面包含登录相关内容，但不在登录URL，可能是登录后的重定向
                    # 进一步检查是否有用户信息
                    if 'user' not in page_text and 'people' not in page_text:
                        return False
            except:
                pass
            
            # 默认返回False，需要登录（保守策略）
            return False
        except Exception as e:
            logger.debug(f"检查登录状态时出错: {e}")
            return False
    
    def login(self, wait_time=15):
        """
        登录知乎（直接打开登录页面，不加载Cookie）
        :param wait_time: 等待扫码登录的时间（秒），默认15秒
        """
        try:
            logger.info("开始登录流程...")
            logger.info("直接打开登录页面，请使用手机知乎APP扫码登录...")
            
            # 直接打开登录页面
            self.driver.get("https://www.zhihu.com/signin")
            self.random_delay(3, 4)
            
            # 尝试点击"扫码登录"标签（如果存在）
            try:
                # 尝试多种选择器来找到扫码登录标签
                qr_selectors = [
                    ".SignFlow-tab[data-za-detail-view-element_name='扫码登录']",
                    ".SignFlow-tabs .SignFlow-tab:last-child",
                    "[aria-label*='扫码']",
                    "button:contains('扫码')"
                ]
                
                qr_tab = None
                for selector in qr_selectors:
                    try:
                        if ':contains(' in selector:
                            # 使用XPath代替contains
                            elements = self.driver.find_elements(By.XPATH, 
                                "//button[contains(text(), '扫码')] | //div[contains(text(), '扫码')]")
                            if elements:
                                qr_tab = elements[0]
                                break
                        else:
                            qr_tab = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                    except:
                        continue
                
                if qr_tab:
                    qr_tab.click()
                    self.random_delay(1, 2)
                    logger.info("已切换到扫码登录")
                else:
                    logger.info("使用默认登录方式（可能是扫码登录）")
            except Exception as e:
                # 如果没有找到扫码登录标签，可能默认就是扫码登录页面
                logger.info(f"使用默认登录方式（可能是扫码登录）: {e}")
            
            # 等待用户扫码登录
            logger.info("=" * 60)
            logger.info("请使用手机知乎APP扫描页面上的二维码进行登录")
            logger.info(f"程序将等待 {wait_time} 秒，请在此期间完成扫码登录")
            logger.info("=" * 60)
            
            # 轮询检查登录状态
            check_interval = 2  # 每2秒检查一次
            elapsed_time = 0
            
            while elapsed_time < wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval
                
                # 检查是否已登录
                if self.check_login_status():
                    logger.info("登录成功！")
                    # 保存Cookie
                    self.save_cookies()
                    return True
                
                # 显示剩余时间
                remaining = wait_time - elapsed_time
                if remaining > 0 and remaining % 10 == 0:
                    logger.info(f"等待中... 还剩 {remaining} 秒")
            
            # 超时后再次检查
            if self.check_login_status():
                logger.info("登录成功！")
                self.save_cookies()
                return True
            else:
                logger.warning(f"等待 {wait_time} 秒后仍未检测到登录，可能登录失败")
                logger.warning("您可以：")
                logger.warning("1. 增加等待时间（修改 wait_time 参数）")
                logger.warning("2. 手动确认是否已登录成功")
                
                # 询问用户是否已登录
                user_input = input("是否已完成登录？(y/n，默认y): ").strip().lower()
                if user_input == '' or user_input == 'y':
                    if self.check_login_status():
                        logger.info("登录确认成功！")
                        self.save_cookies()
                        return True
                    else:
                        logger.warning("未检测到登录状态，请重新运行程序")
                        return False
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False
    
    def random_delay(self, min_seconds=1, max_seconds=2):
        """随机延迟1-2秒"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scroll_page(self, scroll_times=3):
        """向下滚动页面"""
        for _ in range(scroll_times):
            self.driver.execute_script("window.scrollBy(0, 500);")
            self.random_delay(0.5, 1)
    
    def search_keyword(self, keyword):
        """
        搜索关键词
        :param keyword: 搜索关键词
        """
        try:
            logger.info(f"开始搜索关键词: {keyword}")
            self.driver.get("https://www.zhihu.com/search")
            self.random_delay(2, 3)
            
            # 等待搜索框出现并可见可交互
            search_input = None
            search_selectors = [
                "input[placeholder*='搜索']",
                "input[type='search']",
                ".Input-wrapper input",
                ".SearchBar-input input",
                "input.SearchInput-input"
            ]
            
            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if search_input:
                        break
                except TimeoutException:
                    continue
            
            if not search_input:
                # 如果找不到可点击的元素，尝试使用JavaScript
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], .Input-wrapper input")
                    # 滚动到元素可见
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                    self.random_delay(1, 1.5)
                except:
                    raise Exception("无法找到搜索框")
            
            # 确保元素可见和可交互
            try:
                # 先点击聚焦
                self.driver.execute_script("arguments[0].focus();", search_input)
                self.random_delay(0.5, 1)
                
                # 清空并输入
                search_input.clear()
                self.random_delay(0.3, 0.5)
                search_input.send_keys(keyword)
                self.random_delay(1, 1.5)
                
                # 按回车或点击搜索按钮
                try:
                    search_input.send_keys(Keys.RETURN)
                except:
                    # 如果回车不行，尝试点击搜索按钮
                    try:
                        search_btn = self.driver.find_element(By.CSS_SELECTOR, 
                            "button[type='submit'], .SearchBar-searchButton, button.SearchBar-searchButton")
                        self.driver.execute_script("arguments[0].click();", search_btn)
                    except:
                        search_input.send_keys(Keys.RETURN)
                
            except Exception as e:
                # 如果普通方法失败，使用JavaScript直接设置值
                logger.warning(f"使用普通方法输入失败，尝试JavaScript方法: {e}")
                # 转义单引号避免JavaScript错误
                escaped_keyword = keyword.replace("'", "\\'")
                self.driver.execute_script(f"arguments[0].value = '{escaped_keyword}';", search_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
                self.random_delay(1, 1.5)
                try:
                    search_input.send_keys(Keys.RETURN)
                except:
                    # 如果回车也不行，尝试找到并点击搜索按钮
                    try:
                        search_btn = self.driver.find_element(By.CSS_SELECTOR, 
                            "button[type='submit'], .SearchBar-searchButton")
                        self.driver.execute_script("arguments[0].click();", search_btn)
                    except:
                        pass
            
            # 等待搜索结果加载
            self.random_delay(3, 4)
            logger.info(f"搜索完成: {keyword}")
            
        except Exception as e:
            logger.error(f"搜索关键词失败: {e}")
            raise
    
    def extract_post_data(self, post_element):
        """
        提取单个帖子的数据
        :param post_element: 帖子元素
        :return: 帖子数据字典
        """
        post_data = {
            'post_link': '',
            'post_content': '',
            'comments': []
        }
        
        try:
            # 提取帖子链接
            try:
                link_element = post_element.find_element(By.CSS_SELECTOR, "a[href*='/question/'], a[href*='/answer/'], a[href*='/p/']")
                post_data['post_link'] = link_element.get_attribute('href')
            except NoSuchElementException:
                try:
                    link_element = post_element.find_element(By.CSS_SELECTOR, "a")
                    href = link_element.get_attribute('href')
                    if href and ('/question/' in href or '/answer/' in href or '/p/' in href):
                        post_data['post_link'] = href
                except:
                    pass
            
            # 提取帖子内容
            try:
                # 尝试多种选择器来获取帖子内容
                content_selectors = [
                    ".RichContent-inner",
                    ".ContentItem-title",
                    ".SearchResult-title",
                    ".SearchResult-content",
                    "[data-za-detail-view-element_name='Title']"
                ]
                
                for selector in content_selectors:
                    try:
                        content_element = post_element.find_element(By.CSS_SELECTOR, selector)
                        post_data['post_content'] = content_element.text.strip()
                        if post_data['post_content']:
                            break
                    except NoSuchElementException:
                        continue
                
                # 如果还没找到，尝试获取整个元素的文本
                if not post_data['post_content']:
                    post_data['post_content'] = post_element.text.strip()[:500]  # 限制长度
                    
            except Exception as e:
                logger.debug(f"提取帖子内容失败: {e}")
            
            # 提取评论（在搜索结果页面可能没有完整评论，需要点击进入详情页）
            try:
                comment_elements = post_element.find_elements(By.CSS_SELECTOR, ".CommentItem, .Comment-content")
                for comment_elem in comment_elements[:5]:  # 最多提取5条评论
                    comment_text = comment_elem.text.strip()
                    if comment_text:
                        post_data['comments'].append(comment_text)
            except:
                pass
                
        except Exception as e:
            logger.debug(f"提取帖子数据时出错: {e}")
        
        return post_data
    
    def get_post_comments(self, post_url):
        """
        进入帖子详情页获取评论
        :param post_url: 帖子链接
        :return: 评论列表
        """
        comments = []
        try:
            # 保存当前窗口句柄
            original_window = self.driver.current_window_handle
            
            # 打开新标签页
            self.driver.execute_script(f"window.open('{post_url}', '_blank');")
            self.random_delay(2, 3)
            
            # 切换到新标签页
            windows = self.driver.window_handles
            if len(windows) > 1:
                self.driver.switch_to.window(windows[-1])
                
                # 滚动页面加载评论
                self.scroll_page(5)
                self.random_delay(2, 3)
                
                # 尝试点击"展开更多评论"按钮
                try:
                    more_comments_btn = self.driver.find_element(By.CSS_SELECTOR, 
                        ".Comments-container .Button, .CommentList-moreButton, [aria-label*='更多']")
                    if more_comments_btn.is_displayed():
                        # 滚动到按钮可见
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", more_comments_btn)
                        self.random_delay(1, 1.5)
                        try:
                            more_comments_btn.click()
                        except:
                            # 如果普通点击失败，使用JavaScript点击
                            self.driver.execute_script("arguments[0].click();", more_comments_btn)
                        self.random_delay(2, 3)
                        self.scroll_page(3)
                except:
                    pass
                
                # 提取评论
                comment_selectors = [
                    ".CommentItem .CommentItem-content",
                    ".CommentItem .RichText",
                    ".Comment-content",
                    ".CommentItem"
                ]
                
                for selector in comment_selectors:
                    try:
                        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if comment_elements:
                            for elem in comment_elements[:20]:  # 最多提取20条评论
                                comment_text = elem.text.strip()
                                if comment_text and len(comment_text) > 5:  # 过滤太短的文本
                                    comments.append(comment_text)
                            if comments:
                                break
                    except:
                        continue
                
                # 关闭当前标签页，切换回原窗口
                self.driver.close()
                self.driver.switch_to.window(original_window)
                self.random_delay(1, 1.5)
                
        except Exception as e:
            logger.debug(f"获取评论失败 {post_url}: {e}")
            # 确保切换回原窗口
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass
        
        return comments
    
    def crawl_posts(self, keyword, max_posts=20, get_comments=True):
        """
        爬取帖子数据
        :param keyword: 搜索关键词
        :param max_posts: 最大爬取帖子数量
        :param get_comments: 是否获取详细评论
        """
        try:
            self.search_keyword(keyword)
            
            # 等待搜索结果加载
            self.random_delay(3, 4)
            
            # 滚动页面加载更多结果
            for scroll_round in range(5):
                self.scroll_page(3)
                self.random_delay(2, 3)
            
            # 查找所有帖子元素
            post_selectors = [
                ".List-item",
                ".ContentItem",
                ".SearchResult",
                "[data-za-detail-view-element_name='SearchResult']"
            ]
            
            post_elements = []
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        post_elements = elements
                        logger.info(f"找到 {len(elements)} 个帖子元素")
                        break
                except:
                    continue
            
            if not post_elements:
                logger.warning("未找到帖子元素，尝试通用选择器")
                # 尝试更通用的选择器
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='Item'], div[class*='Result'], div[class*='Card']")
            
            logger.info(f"开始提取 {min(len(post_elements), max_posts)} 个帖子数据")
            
            # 提取帖子数据
            for idx, post_elem in enumerate(post_elements[:max_posts]):
                try:
                    logger.info(f"正在处理第 {idx + 1}/{min(len(post_elements), max_posts)} 个帖子")
                    
                    # 滚动到元素可见
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", post_elem)
                    self.random_delay(1, 2)
                    
                    # 提取基础数据
                    post_data = self.extract_post_data(post_elem)
                    
                    # 如果需要获取详细评论且有链接
                    if get_comments and post_data['post_link']:
                        logger.info(f"正在获取评论: {post_data['post_link']}")
                        comments = self.get_post_comments(post_data['post_link'])
                        if comments:
                            post_data['comments'] = comments
                    
                    # 只保存有链接或内容的帖子
                    if post_data['post_link'] or post_data['post_content']:
                        post_data['keyword'] = keyword
                        self.results.append(post_data)
                        logger.info(f"成功提取帖子: {post_data['post_link'][:50]}...")
                    
                    self.random_delay(1, 2)
                    
                except Exception as e:
                    logger.error(f"处理帖子时出错: {e}")
                    continue
            
            logger.info(f"关键词 '{keyword}' 爬取完成，共获取 {len([r for r in self.results if r.get('keyword') == keyword])} 个帖子")
            
        except Exception as e:
            logger.error(f"爬取过程出错: {e}")
            raise
    
    def save_to_excel(self, filename='data/zhihu_results.xlsx'):
        """
        保存结果到Excel文件
        :param filename: 输出文件名
        """
        if not self.results:
            logger.warning("没有数据可保存")
            return
        
        # 准备Excel数据
        excel_data = []
        for result in self.results:
            row = {
                '关键词': result.get('keyword', ''),
                '帖子链接': result.get('post_link', ''),
                '帖子内容': result.get('post_content', ''),
                '评论数量': len(result.get('comments', [])),
            }
            
            # 将评论合并为字符串（用分号分隔）
            comments = result.get('comments', [])
            if comments:
                # 将多条评论合并，每条评论用换行符分隔
                row['用户评论'] = '\n'.join(comments[:10])  # 最多保存10条评论
            else:
                row['用户评论'] = ''
            
            excel_data.append(row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(excel_data)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"数据已保存到 {filename}，共 {len(excel_data)} 条记录")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


def main():
    """主函数"""
    # 搜索关键词列表
    keywords = ["加塞 心态调整"]
    
    crawler = ZhihuCrawler(headless=False)  # 设置为True使用无头模式
    
    try:
        # 初始化浏览器
        crawler.init_driver()
        
        # 直接登录（不检查Cookie，直接打开登录页面）
        logger.info("打开登录页面，请扫码登录...")
        # 等待60秒供用户扫码登录，可以根据需要调整时间
        if not crawler.login(wait_time=60):
            logger.error("登录失败，程序退出")
            return
        
        # 遍历每个关键词进行爬取
        for keyword in keywords:
            try:
                crawler.crawl_posts(keyword, max_posts=20, get_comments=True)
                # 关键词之间稍作延迟
                time.sleep(3)
            except Exception as e:
                logger.error(f"爬取关键词 '{keyword}' 时出错: {e}")
                continue
        
        # 保存结果
        crawler.save_to_excel('data/zhihu_results.xlsx')
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
    finally:
        crawler.close()


if __name__ == "__main__":
    main()

