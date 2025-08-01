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
    """使用Jina Reader API读取URL内容并返回Markdown格式的文本
    
    Args:
        url: 要读取的URL
        
    Returns:
        网页内容（Markdown格式）或错误信息
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
    """使用Jina Search API执行网页搜索并返回结果
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        搜索结果（Markdown格式）或错误信息
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
