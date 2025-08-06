"""免费的网页抓取工具 - 替代Jina API"""
import requests
import os
import hashlib
from typing import Optional
from urllib.parse import urlparse, urljoin
from langchain_core.tools import tool
from bs4 import BeautifulSoup
import time
import json

class FreeWebScrapingHelper:
    """免费网页抓取辅助类"""
    
    def __init__(self, max_content_length: int = 2000, work_dir: str = None):
        self.max_content_length = max_content_length
        self.work_dir = work_dir or "output"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _trim_content(self, content: str) -> str:
        """裁剪内容到最大允许长度"""
        if len(content) > self.max_content_length:
            truncated = content[:self.max_content_length]
            return truncated + "... (content truncated)"
        return content
    
    @staticmethod
    def _generate_file_name_from_url(url: str, max_length=255) -> str:
        """从URL生成文件名"""
        url_bytes = url.encode("utf-8")
        hash_value = hashlib.blake2b(url_bytes).hexdigest()
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        file_name = f"{domain}_{hash_value[:8]}.md"
        return file_name
    
    def _html_to_markdown(self, html_content: str, url: str) -> str:
        """将HTML转换为Markdown格式"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # 提取标题
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "无标题"
        
        # 提取主要内容
        content_selectors = [
            'article', 'main', '.content', '.post-content', 
            '.article-content', '.entry-content', '#content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body') or soup
        
        # 转换为Markdown
        markdown_content = f"# {title_text}\n\n"
        markdown_content += f"**URL来源**: {url}\n\n"
        
        # 提取段落和标题
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
            text = element.get_text().strip()
            if not text:
                continue
                
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                markdown_content += f"\n{'#' * level} {text}\n\n"
            elif element.name == 'li':
                markdown_content += f"- {text}\n"
            elif len(text) > 10:  # 只保留有意义的文本
                markdown_content += f"{text}\n\n"
        
        return markdown_content

# 创建全局辅助实例
_free_scraper = FreeWebScrapingHelper()

@tool
def free_url_reader(url: str) -> str:
    """读取网页内容并转换为Markdown格式
    
    这个工具用于高质量的网页内容提取：
    - 使用requests和BeautifulSoup抓取网页
    - 自动清理HTML标签，提取核心文本内容
    - 转换为易读的Markdown格式并自动保存
    - 处理各种网页类型：新闻、博客、文档等
    
    Args:
        url: 要读取的网页URL
            - 支持HTTP和HTTPS协议
            - 可以是新闻网站、博客、官方文档等
            - 例如："https://example.com/article"
            - 工具会自动处理编码和格式问题
        
    Returns:
        Markdown格式的网页内容，包括：
        - 清洁的文本内容，去除广告和无关元素
        - 保留标题、段落、列表等结构
        - 自动保存到文件，返回内容摘要
        - 如果抓取失败，返回详细的错误信息
        
    使用场景：
    - 抓取新闻文章进行分析
    - 获取产品信息和评价
    - 收集研究资料
    - 监控网站内容变化
    
    """
    try:
        print(f"🌐 正在抓取: {url}")
        
        # 发送请求
        response = requests.get(url, headers=_free_scraper.headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # 自动检测编码
        
        # 转换为Markdown
        markdown_content = _free_scraper._html_to_markdown(response.text, url)
        
        # 保存完整内容到文件
        # if markdown_content:
        #     filename = _free_scraper._generate_file_name_from_url(url)
        #     save_path = os.path.join(_free_scraper.work_dir, filename)
        #     os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
        #     with open(save_path, 'w', encoding='utf-8') as f:
        #         f.write(markdown_content)
        #     print(f"💾 内容已保存到: {filename}")
        
        # 返回截断的内容预览
        result = _free_scraper._trim_content(markdown_content)
        return result
        
    except requests.exceptions.RequestException as e:
        return f"网络请求错误: {str(e)}"
    except Exception as e:
        return f"抓取网页时出错: {str(e)}"

@tool
def free_search(query: str, num_results: int = 5) -> str:
    """使用搜索API执行网页搜索

    这个工具提供网页搜索功能：
    - 使用DuckDuckGo搜索引擎
    - 返回相关性强的搜索结果
    - 自动过滤和整理搜索结果
    - 支持中英文搜索
    
    Args:
        query: 搜索查询字符串
              - 可以是关键词：例如"36kr 创投 融资"
              - 可以是问题：例如"36氪最新融资新闻"
              - 可以是具体需求：例如"36kr创投平台官网"
              - 支持复杂查询和中文搜索
        num_results: 返回结果数量（默认5个）
        
    Returns:
        JSON格式的搜索结果，包括：
        - 多个相关网页的标题、摘要和链接
        - 按相关性排序的结果列表
        - 自动保存搜索结果到文件
        - 如果搜索失败，返回错误详情
        
    使用场景：
    - 搜索特定网站的页面
    - 查找新闻和资讯
    - 收集行业信息
    - 寻找官方网站和资源
    
    """
    try:
        from duckduckgo_search import DDGS
        
        print(f"🔍 正在搜索: {query}")
        
        # 使用DuckDuckGo搜索
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        
        if not results:
            return "未找到相关搜索结果"
        
        # 格式化搜索结果
        formatted_results = {
            "query": query,
            "results": []
        }
        
        for i, result in enumerate(results, 1):
            formatted_result = {
                "rank": i,
                "title": result.get('title', '无标题'),
                "url": result.get('href', ''),
                "description": result.get('body', '无描述'),
            }
            formatted_results["results"].append(formatted_result)
        
        # 保存搜索结果
        # search_filename = f"search_{hashlib.md5(query.encode()).hexdigest()[:8]}.json"
        # search_path = os.path.join(_free_scraper.work_dir, search_filename)
        # os.makedirs(os.path.dirname(search_path), exist_ok=True)
        
        # with open(search_path, 'w', encoding='utf-8') as f:
        #     json.dump(formatted_results, f, ensure_ascii=False, indent=2)
        
        # print(f"💾 搜索结果已保存到: {search_filename}")
        
        # 返回格式化的结果
        result_text = f"搜索查询: {query}\n\n"
        for result in formatted_results["results"]:
            result_text += f"{result['rank']}. **{result['title']}**\n"
            result_text += f"   URL: {result['url']}\n"
            result_text += f"   描述: {result['description']}\n\n"
        
        return _free_scraper._trim_content(result_text)
        
    except ImportError:
        return "错误: 需要安装 duckduckgo-search 库。请运行: pip install duckduckgo-search"
    except Exception as e:
        return f"搜索时出错: {str(e)}"
