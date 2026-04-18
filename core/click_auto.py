"""
知乎自动点击脚本
用于学术研究目的，自动点击搜索结果并获取评论
"""

import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZhihuAutoClicker:
    def __init__(self, headless=False, cookie_file='zhihu_cookies.json'):
        """
        初始化自动点击器
        :param headless: 是否使用无头模式
        :param cookie_file: Cookie保存文件路径
        """
        self.driver = None
        self.headless = headless
        self.cookie_file = cookie_file
        self.clicked_posts = set()  # 记录已点击的帖子链接
        
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
            current_url = self.driver.current_url
            if 'signin' in current_url.lower() or 'login' in current_url.lower():
                return False
            
            # 检查用户信息
            try:
                user_selectors = [
                    ".AppHeader-userInfo",
                    ".AppHeader-profile",
                    "[data-za-detail-view-element_name='UserAvatar']",
                    "a[href*='/people/']"
                ]
                for selector in user_selectors:
                    try:
                        user_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if user_elements:
                            for elem in user_elements:
                                if elem.is_displayed():
                                    return True
                    except:
                        continue
            except:
                pass
            
            return False
        except Exception as e:
            logger.debug(f"检查登录状态时出错: {e}")
            return False
    
    def login(self, wait_time=60):
        """登录知乎"""
        try:
            logger.info("开始登录流程...")
            self.driver.get("https://www.zhihu.com/signin")
            self.random_delay(3, 4)
            
            # 尝试切换到扫码登录
            try:
                qr_tab = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '扫码')] | //div[contains(text(), '扫码')]"))
                )
                qr_tab.click()
                self.random_delay(1, 2)
                logger.info("已切换到扫码登录")
            except:
                logger.info("使用默认登录方式")
            
            logger.info("=" * 60)
            logger.info("请使用手机知乎APP扫描页面上的二维码进行登录")
            logger.info(f"程序将等待 {wait_time} 秒，请在此期间完成扫码登录")
            logger.info("=" * 60)
            
            check_interval = 2
            elapsed_time = 0
            
            while elapsed_time < wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval
                
                if self.check_login_status():
                    logger.info("登录成功！")
                    self.save_cookies()
                    return True
                
                remaining = wait_time - elapsed_time
                if remaining > 0 and remaining % 10 == 0:
                    logger.info(f"等待中... 还剩 {remaining} 秒")
            
            if self.check_login_status():
                logger.info("登录成功！")
                self.save_cookies()
                return True
            else:
                logger.warning(f"等待 {wait_time} 秒后仍未检测到登录")
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
    
    def random_delay(self, min_seconds=1, max_seconds=2):
        """随机延迟"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scroll_down(self, pixels=500):
        """向下滚动页面"""
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
        self.random_delay(0.5, 1)
    
    def search_keyword(self, keyword):
        """搜索关键词"""
        try:
            logger.info(f"开始搜索关键词: {keyword}")
            self.driver.get("https://www.zhihu.com/search")
            self.random_delay(2, 3)
            
            # 查找搜索框
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
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], .Input-wrapper input")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                    self.random_delay(1, 1.5)
                except:
                    raise Exception("无法找到搜索框")
            
            # 输入关键词
            try:
                self.driver.execute_script("arguments[0].focus();", search_input)
                self.random_delay(0.5, 1)
                search_input.clear()
                self.random_delay(0.3, 0.5)
                search_input.send_keys(keyword)
                self.random_delay(1, 1.5)
                search_input.send_keys(Keys.RETURN)
            except Exception as e:
                logger.warning(f"使用普通方法输入失败，尝试JavaScript方法: {e}")
                escaped_keyword = keyword.replace("'", "\\'")
                self.driver.execute_script(f"arguments[0].value = '{escaped_keyword}';", search_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
                self.random_delay(1, 1.5)
                search_input.send_keys(Keys.RETURN)
            
            # 等待搜索结果加载
            self.random_delay(3, 4)
            logger.info(f"搜索完成: {keyword}")
            
        except Exception as e:
            logger.error(f"搜索关键词失败: {e}")
            raise
    
    def get_post_links(self):
        """获取当前页面的所有帖子链接"""
        post_links = []
        try:
            # 查找所有帖子元素
            post_selectors = [
                ".List-item",
                ".ContentItem",
                ".SearchResult",
                "[data-za-detail-view-element_name='SearchResult']",
                "div[class*='Item']"
            ]
            
            post_elements = []
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        post_elements = elements
                        break
                except:
                    continue
            
            # 从每个帖子元素中提取链接
            for post_elem in post_elements:
                try:
                    # 查找链接
                    link_selectors = [
                        "a[href*='/question/']",
                        "a[href*='/answer/']",
                        "a[href*='/p/']",
                        "a[href*='/post/']"
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = post_elem.find_element(By.CSS_SELECTOR, selector)
                            href = link_elem.get_attribute('href')
                            if href and href not in self.clicked_posts:
                                post_links.append({
                                    'element': link_elem,
                                    'url': href
                                })
                                break
                        except NoSuchElementException:
                            continue
                except:
                    continue
            
            logger.info(f"找到 {len(post_links)} 个未点击的帖子")
            return post_links
            
        except Exception as e:
            logger.error(f"获取帖子链接失败: {e}")
            return []
    
    def click_view_all_answers(self):
        """在问题页点击“查看全部…个回答/答案”按钮"""
        try:
            # 等页面主体加载出来
            self.random_delay(1.5, 2.5)

            # 常见样式：问题标题下方的“查看全部 xx 个回答/答案”
            # 使用 XPath 直接匹配文本
            xpath_list = [
                "//button[contains(text(), '查看全部') and contains(text(), '个回答')]",
                "//button[contains(text(), '查看全部') and contains(text(), '个答案')]",
                "//a[contains(text(), '查看全部') and contains(text(), '个回答')]",
                "//a[contains(text(), '查看全部') and contains(text(), '个答案')]",
                "//span[contains(text(), '查看全部') and contains(text(), '个回答')]/ancestor::button",
                "//span[contains(text(), '查看全部') and contains(text(), '个答案')]/ancestor::button",
            ]

            clicked = False
            for xp in xpath_list:
                try:
                    elems = self.driver.find_elements(By.XPATH, xp)
                    for btn in elems:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                # 滚动到按钮
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                self.random_delay(0.8, 1.3)
                                try:
                                    btn.click()
                                except Exception:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                clicked = True
                                logger.info("已点击“查看全部…个回答/答案”按钮")
                                # 等待回答列表刷新
                                self.random_delay(2, 3)
                                break
                        except Exception:
                            continue
                    if clicked:
                        break
                except Exception:
                    continue

            if not clicked:
                logger.info("未找到“查看全部…个回答/答案”按钮，可能当前已是完整回答列表")

        except Exception as e:
            logger.debug(f"点击“查看全部…个回答/答案”按钮时出错: {e}")

    def expand_all_comments(self):
        """展开所有评论"""
        try:
            # 滚动到评论区域
            self.scroll_down(300)
            self.random_delay(1, 1.5)
            
            # 查找并点击"展开更多评论"按钮
            more_comment_selectors = [
                "button:contains('展开')",
                "button:contains('更多')",
                ".CommentList-moreButton",
                "[aria-label*='更多']",
                "[aria-label*='展开']",
                ".Comments-container .Button",
                "button.Button--plain"
            ]
            
            max_clicks = 10  # 最多点击10次，避免无限循环
            click_count = 0
            
            while click_count < max_clicks:
                clicked = False
                
                # 尝试使用XPath查找包含"展开"或"更多"的按钮
                try:
                    expand_buttons = self.driver.find_elements(By.XPATH, 
                        "//button[contains(text(), '展开') or contains(text(), '更多') or contains(text(), '查看')]")
                    
                    for btn in expand_buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                # 滚动到按钮可见
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                self.random_delay(0.5, 1)
                                
                                # 点击按钮
                                try:
                                    btn.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                
                                clicked = True
                                click_count += 1
                                self.random_delay(1, 2)
                                
                                # 滚动一下加载新内容
                                self.scroll_down(200)
                                self.random_delay(0.5, 1)
                                break
                        except:
                            continue
                except:
                    pass
                
                # 如果没找到可点击的按钮，尝试查找评论区域的展开按钮
                if not clicked:
                    try:
                        comment_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".Comments-container, .CommentList, .CommentItem")
                        
                        for container in comment_containers:
                            try:
                                buttons = container.find_elements(By.CSS_SELECTOR, "button")
                                for btn in buttons:
                                    try:
                                        btn_text = btn.text.strip()
                                        if btn_text and ('展开' in btn_text or '更多' in btn_text or '查看' in btn_text):
                                            if btn.is_displayed() and btn.is_enabled():
                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                self.random_delay(0.5, 1)
                                                
                                                try:
                                                    btn.click()
                                                except:
                                                    self.driver.execute_script("arguments[0].click();", btn)
                                                
                                                clicked = True
                                                click_count += 1
                                                self.random_delay(1, 2)
                                                self.scroll_down(200)
                                                self.random_delay(0.5, 1)
                                                break
                                    except:
                                        continue
                                
                                if clicked:
                                    break
                            except:
                                continue
                    except:
                        pass
                
                if not clicked:
                    break
            
            logger.info(f"共点击了 {click_count} 次展开按钮")
            
        except Exception as e:
            logger.debug(f"展开评论时出错: {e}")
    
    def get_all_comments(self):
        """获取所有评论内容"""
        comments = []
        try:
            # 先展开所有评论
            self.expand_all_comments()
            
            # 滚动页面确保所有评论都加载
            for _ in range(5):
                self.scroll_down(500)
                self.random_delay(0.5, 1)
            
            # 提取评论
            comment_selectors = [
                ".CommentItem .CommentItem-content",
                ".CommentItem .RichText",
                ".Comment-content",
                ".CommentItem-content",
                ".CommentItem"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comment_elements:
                        for elem in comment_elements:
                            try:
                                comment_text = elem.text.strip()
                                if comment_text and len(comment_text) > 5:  # 过滤太短的文本
                                    if comment_text not in comments:  # 去重
                                        comments.append(comment_text)
                            except:
                                continue
                        
                        if comments:
                            break
                except:
                    continue
            
            logger.info(f"获取到 {len(comments)} 条评论")
            return comments
            
        except Exception as e:
            logger.error(f"获取评论失败: {e}")
            return []
    
    def click_post_and_get_comments(self, post_info):
        """点击帖子并获取评论"""
        try:
            post_url = post_info['url']
            post_element = post_info['element']
            
            logger.info(f"正在点击帖子: {post_url[:60]}...")
            
            # 保存当前窗口句柄
            original_window = self.driver.current_window_handle
            
            # 点击帖子链接（在新标签页打开）
            try:
                # 使用JavaScript在新标签页打开
                self.driver.execute_script(f"window.open('{post_url}', '_blank');")
            except:
                # 如果JavaScript失败，尝试直接点击
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
                    self.random_delay(0.5, 1)
                    post_element.click()
                except:
                    self.driver.execute_script("arguments[0].click();", post_element)
            
            # 等待新标签页打开
            self.random_delay(2, 3)
            
            # 切换到新标签页
            windows = self.driver.window_handles
            if len(windows) > 1:
                self.driver.switch_to.window(windows[-1])
                
                # 等待页面加载
                self.random_delay(2, 3)

                # 优先点击“查看全部…个回答/答案”，避免只看到部分回答
                self.click_view_all_answers()
                
                # 获取所有评论
                comments = self.get_all_comments()
                
                # 关闭当前标签页
                self.driver.close()
                
                # 切换回原窗口
                self.driver.switch_to.window(original_window)
                self.random_delay(1, 1.5)
                
                # 标记为已点击
                self.clicked_posts.add(post_url)
                
                logger.info(f"成功获取 {len(comments)} 条评论")
                return comments
            else:
                logger.warning("未能打开新标签页")
                return []
                
        except Exception as e:
            logger.error(f"点击帖子并获取评论失败: {e}")
            # 确保切换回原窗口
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass
            return []
    
    def auto_click_posts(self, keyword, max_rounds=5):
        """
        自动点击帖子列表
        :param keyword: 搜索关键词
        :param max_rounds: 最大滚动轮数
        """
        try:
            # 搜索关键词
            self.search_keyword(keyword)
            
            # 开始自动点击循环
            for round_num in range(max_rounds):
                logger.info(f"========== 第 {round_num + 1} 轮点击 ==========")
                
                # 获取当前页面的帖子链接
                post_links = self.get_post_links()
                
                if not post_links:
                    logger.info("当前页面没有更多未点击的帖子，向下滚动...")
                    # 向下滚动刷新列表
                    for _ in range(3):
                        self.scroll_down(800)
                        self.random_delay(1, 1.5)
                    
                    # 等待新内容加载
                    self.random_delay(2, 3)
                    
                    # 再次获取帖子链接
                    post_links = self.get_post_links()
                
                # 点击每个帖子
                for idx, post_info in enumerate(post_links):
                    logger.info(f"正在处理第 {idx + 1}/{len(post_links)} 个帖子")
                    
                    # 点击延迟1-2秒
                    self.random_delay(1, 2)
                    
                    # 点击帖子并获取评论
                    comments = self.click_post_and_get_comments(post_info)
                    
                    # 点击延迟1-2秒
                    self.random_delay(1, 2)
                
                # 向下滚动刷新列表
                logger.info("向下滚动刷新列表...")
                for _ in range(3):
                    self.scroll_down(800)
                    self.random_delay(1, 1.5)
                
                # 等待新内容加载
                self.random_delay(2, 3)
                
                logger.info(f"第 {round_num + 1} 轮完成，共点击了 {len(post_links)} 个帖子")
            
            logger.info("自动点击完成！")
            
        except Exception as e:
            logger.error(f"自动点击过程出错: {e}")
            raise
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


def main():
    """主函数"""
    keyword = "座舱ai 陪聊"
    
    clicker = ZhihuAutoClicker(headless=False)
    
    try:
        # 初始化浏览器
        clicker.init_driver()
        
        # 尝试加载Cookie
        if not clicker.load_cookies() or not clicker.check_login_status():
            logger.info("需要登录...")
            if not clicker.login(wait_time=60):
                logger.error("登录失败，程序退出")
                return
        
        # 开始自动点击
        clicker.auto_click_posts(keyword, max_rounds=5)
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
    finally:
        clicker.close()


if __name__ == "__main__":
    main()

