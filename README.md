# 知乎检索词爬虫

用于学术研究目的，使用Selenium爬取知乎特定检索词的帖子和用户评论，支持多种爬取方式和数据提取方法。

## 项目结构

```
selenium_crawl/
├── core/                   # 核心爬虫文件
│   ├── click_auto.py       # 自动点击脚本
│   ├── har_address.py      # 从HAR文件提取数据
│   ├── zhihu_crawler.py    # 知乎爬虫主文件
├── tools/                  # 辅助工具文件
│   ├── check_feeds.py      # 检查feeds API
│   ├── check_har.py        # 检查HAR文件
│   ├── check_har2.py       # 检查HAR文件（版本2）
│   ├── check_missing_titles.py # 检查缺失标题
│   ├── check_search_api.py # 检查搜索API
│   ├── find_all_apis.py    # 查找所有API
│   └── test.py             # 测试文件
├── data/                   # 数据文件
│   ├── test.har            # 测试用HAR文件
│   ├── zhihu_har_results.xlsx  # HAR提取结果
│   ├── zhihu_results.xlsx  # 爬虫结果
├── 存/                     # 存储目录
│   ├── xhs_har_address.py  # 小红书HAR处理
│   ├── zhihu_cookies.json  # 知乎Cookie文件
├── __pycache__/            # 编译缓存
├── .gitignore              # Git忽略文件
├── README.md               # 项目说明
├── requirements.txt        # 依赖文件
```

## 爬虫时需要用到的文件

### 核心爬虫文件
1. **core/click_auto.py**：自动点击脚本，用于模拟用户点击行为并获取评论（推荐使用）
2. **core/har_address.py**：从HAR文件提取数据的工具（推荐使用）
3. **core/zhihu_crawler.py**：主要爬虫文件，用于爬取特定检索词的帖子和评论

### 配置和依赖文件
4. **requirements.txt**：项目依赖
5. **zhihu_cookies.json**：保存登录Cookie

### 辅助工具文件
6. **tools/check_har.py**：检查HAR文件中的API响应
7. **tools/check_feeds.py**：检查feeds API结构
8. **tools/check_search_api.py**：检查搜索API结构
9. **tools/find_all_apis.py**：查找所有可能包含数据的API

## 功能特点

1. **自动登录**：支持Cookie自动登录，首次使用可扫码登录，登录信息自动保存
2. **关键词检索**：支持输入多个检索词进行搜索（如"加塞"、"心态调整"）
3. **智能滚动**：自动向下滚动页面加载更多内容
4. **模拟点击**：模拟真实用户行为，点击延迟1-2秒
5. **数据提取**：提取帖子链接、帖子内容、用户评论
6. **Excel导出**：将结果保存到Excel表格，每个帖子一行，不同列存储不同信息
7. **HAR文件支持**：从抓包工具导出的HAR文件中提取数据
8. **自动点击功能**：自动点击搜索结果并获取评论

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用前准备

1. **安装Chrome浏览器**
2. **安装ChromeDriver**：
   - 下载与Chrome版本匹配的ChromeDriver
   - 将ChromeDriver添加到系统PATH，或放在项目目录下
   - 或者使用 `webdriver-manager` 自动管理（可选）
3. **安装抓包工具**（推荐）：
   - Chrome开发者工具（F12）
   - Fiddler
   - Charles
   我用的是reqable

## 推荐使用流程

### 第一步：使用自动滑动点击脚本

1. **配置关键词**：编辑 `core/click_auto.py` 文件中的 `main()` 函数，修改关键词
   ```python
   keyword = "加塞 心态调整"  # 修改为你需要的关键词
   ```

2. **运行脚本**：
   ```bash
   python core/click_auto.py
   ```

3. **登录**：如果Cookie已过期，需要重新扫码登录

4. **自动点击**：程序会自动点击搜索结果，展开评论并获取数据

### 第二步：使用抓包工具获取HAR文件

1. **开启抓包**：在自动点击过程中，使用抓包工具（如Chrome开发者工具）捕获网络请求
2. **导出HAR文件**：
   - 在Chrome开发者工具中，切换到Network选项卡
   - 右键点击任意请求，选择"Save all as HAR with content"
   - 将文件保存到 `data/` 目录，例如 `data/zhihu_data.har`

### 第三步：处理HAR格式的数据

1. **运行HAR处理脚本**：
   ```bash
   python core/har_address.py
   ```

2. **输入HAR文件路径**：根据提示输入HAR文件路径（例如：`data/zhihu_data.har`）

3. **查看结果**：提取完成后，结果会保存在 `data/zhihu_har_results.xlsx` 文件中

## 其他使用方法

### 方法：使用Selenium直接爬取

1. **配置关键词**：编辑 `core/zhihu_crawler.py` 文件中的 `main()` 函数，修改关键词列表
   ```python
   keywords = ["加塞 心态调整"]  # 修改为你需要的关键词
   ```

2. **运行爬虫**：
   ```bash
   python core/zhihu_crawler.py
   ```

3. **首次登录**：
   - 程序会自动打开知乎登录页面
   - 使用手机知乎APP扫描页面上的二维码进行登录
   - 登录成功后，Cookie会自动保存到 `zhihu_cookies.json` 文件

4. **查看结果**：爬取完成后，结果会保存在 `data/zhihu_results.xlsx` 文件中

## 自定义选项

### 自定义爬取数量

在 `core/zhihu_crawler.py` 的 `crawl_posts()` 方法调用中修改 `max_posts` 参数：

```python
crawler.crawl_posts(keyword, max_posts=20, get_comments=True)
```

### 无头模式

如果需要后台运行（不显示浏览器窗口），修改：

```python
crawler = ZhihuCrawler(headless=True)
```

### 自定义等待时间

如果登录等待时间不够，可以修改 `login()` 方法的 `wait_time` 参数：

```python
crawler.login(wait_time=120)  # 等待120秒
```

## 输出格式

### data/zhihu_results.xlsx（直接爬取结果）

- **关键词**：搜索的关键词
- **帖子链接**：知乎帖子/问题的链接
- **帖子内容**：帖子的标题和内容
- **评论数量**：提取到的评论数量
- **用户评论**：用户评论内容（多条评论用换行符分隔）

### data/zhihu_har_results.xlsx（HAR提取结果）

- **帖子内容**：问题标题
- **帖子链接**：知乎问题链接
- **回复1**：第一条回答内容
- **回复2**：第二条回答内容
- **...**：更多回答内容

## 注意事项

1. **登录要求**：程序需要登录后才能正常爬取数据，请确保完成登录流程
2. **Cookie安全**：`zhihu_cookies.json` 文件包含您的登录信息，请妥善保管，不要泄露
3. **遵守网站规则**：本工具仅用于学术研究，请遵守知乎的使用条款和robots.txt
4. **访问频率**：程序已设置合理的延迟，避免对服务器造成压力
5. **反爬虫机制**：知乎可能有反爬虫机制，如遇到验证码或封禁，请适当增加延迟时间
6. **网络环境**：确保网络连接稳定，能够正常访问知乎网站
7. **页面结构变化**：知乎页面结构可能发生变化，导致元素找不到，需要更新选择器

## 常见问题

### ChromeDriver版本不匹配

确保ChromeDriver版本与Chrome浏览器版本匹配。可以访问 [ChromeDriver下载页面](https://chromedriver.chromium.org/downloads) 下载对应版本。

### 找不到元素

知乎页面结构可能发生变化，如果遇到元素找不到的错误，可能需要更新选择器。

### 评论获取不完整

由于知乎的评论加载机制，部分评论可能需要手动滚动或点击"展开更多"才能加载。程序已尝试自动处理，但可能无法获取所有评论。

### 登录相关问题

**问题：程序一直提示未登录**
- 确保已完成扫码登录
- 检查 `zhihu_cookies.json` 文件是否存在且有效
- 如果Cookie过期，删除 `zhihu_cookies.json` 文件后重新运行程序

**问题：登录等待时间不够**
- 修改代码中的 `wait_time` 参数，增加等待时间
- 或者在程序提示时输入 'y' 确认已完成登录

## 许可证

本工具仅用于学术研究目的。