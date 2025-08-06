"""LangGraph版本的Jina工具 - 与原JinaTool保持一致"""
import hashlib
import os
import requests
from typing import Optional
from urllib.parse import urlparse
from langchain_core.tools import tool

class JinaToolHelper:
    """Jina工具辅助类，提供原JinaTool的功能"""
    
    def __init__(self, api_key: Optional[str] = None, max_content_length: int = 800, work_dir: str = None):
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.max_content_length = max_content_length
        self.work_dir = work_dir or "output"
        
    def _get_headers(self) -> dict:
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json',
            'X-With-Generated-Alt': 'true'
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
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
        file_name = os.path.basename(url)
        prefix = f"{parsed_url.netloc}_{file_name}"
        end = hash_value[:min(8, max_length - len(parsed_url.netloc) - len(file_name) - 1)]
        file_name = f"{prefix}_{end}"
        return file_name

# 创建全局辅助实例
_jina_helper = JinaToolHelper()

@tool
def jina_url_reader(url: str) -> str:
    """使用Jina Reader API读取网页内容并转换为Markdown格式
    
    这个工具专门用于高质量的网页内容提取：
    - 自动清理HTML标签，提取核心文本内容
    - 保留网页结构，转换为易读的Markdown格式
    - 自动保存抓取的内容到文件，便于后续分析
    - 处理各种网页类型：新闻、博客、文档、产品页面等
    
    Args:
        url: 要读取的网页URL
            - 支持HTTP和HTTPS协议
            - 可以是新闻网站、博客、官方文档等
            - 例如："https://example.com/article"
            - 工具会自动处理重定向和编码问题
        
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
    
    注意：工具会自动限制内容长度，如需完整内容请查看保存的文件
    """
    try:
        data = {'url': url}
        response = requests.post(
            'https://r.jina.ai/', 
            headers=_jina_helper._get_headers(), 
            json=data,
            timeout=30
        )
        response.raise_for_status()
        content = response.text
        result = _jina_helper._trim_content(content)
        
        # 保存文件（与原版保持一致）
        if content:
            filename = _jina_helper._generate_file_name_from_url(url)
            save_path = os.path.realpath(os.path.join(_jina_helper.work_dir, filename))
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return result
        
    except Exception as e:
        return f"Error reading URL: {str(e)}"

@tool
def jina_search(query: str) -> str:
    """使用Jina Search API执行智能网页搜索
    
    这个工具提供强大的网页搜索功能：
    - 基于AI的智能搜索，理解查询意图
    - 返回高质量、相关性强的搜索结果
    - 自动过滤垃圾信息，提供准确内容
    - 支持中英文搜索，覆盖全球网站
    
    Args:
        query: 搜索查询字符串
              - 可以是关键词：例如"人工智能发展趋势"
              - 可以是问题：例如"如何学习机器学习"
              - 可以是具体需求：例如"2024年最佳手机推荐"
              - 支持复杂查询：例如"Python数据分析库对比"
        
    Returns:
        Markdown格式的搜索结果，包括：
        - 多个相关网页的标题、摘要和链接
        - 按相关性排序的结果列表
        - 自动保存搜索结果到文件
        - 如果搜索失败，返回错误详情
        
    使用场景：
    - 研究特定话题的最新信息
    - 寻找产品评价和对比
    - 收集行业动态和趋势
    - 查找解决方案和教程
    - 获取权威资料和数据
    
    注意：搜索结果会自动保存，便于后续详细分析和引用
    """
    try:
        query = query.strip()
        url = f'https://s.jina.ai/{query}'
        
        headers = {'Accept': 'application/json'}
        if _jina_helper.api_key:
            headers["Authorization"] = f"Bearer {_jina_helper.api_key}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        result = _jina_helper._trim_content(content)
        
        # 保存文件（与原版保持一致）
        if content:
            filename = _jina_helper._generate_file_name_from_url(url)
            save_path = os.path.realpath(os.path.join(_jina_helper.work_dir, filename))
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return result
        
    except Exception as e:
        return f"Error performing search: {str(e)}"
