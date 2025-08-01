"""LangGraph版本的文件操作工具 - 与原FileTool保持一致"""
import os
import json
from pathlib import Path
from langchain_core.tools import tool

class MarkdownConverter:
    """简化的Markdown转换器"""
    def convert(self, file_path: str):
        class Result:
            def __init__(self, content):
                self.text_content = content
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的Markdown格式化
        file_name = Path(file_path).name
        markdown_content = f"""# 文件内容: {file_name}

**文件路径**: `{file_path}`

## 内容

```
{content}
```
"""
        return Result(markdown_content)

@tool
def save_file(contents: str, file_name: str, overwrite: bool = True, save_dir: str = "") -> str:
    """保存内容到文件
    
    Args:
        contents: 要保存的内容
        file_name: 文件名
        overwrite: 是否覆盖已存在的文件
        save_dir: 保存目录，默认为output目录
        
    Returns:
        成功时返回文件名，失败时返回错误信息
    """
    try:
        if save_dir:
            save_dir = Path(save_dir)
        else:
            save_dir = Path("output")
        
        file_path = save_dir.joinpath(file_name)
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.exists() and not overwrite:
            return f"File {file_name} already exists"
        
        file_path.write_text(contents, encoding='utf-8')
        return str(file_name)
    except Exception as e:
        return f"Error saving to file: {e}"

@tool
def read_file(file_name: str) -> str:
    """读取文件内容并转换为Markdown格式
    
    Args:
        file_name: 文件名
        
    Returns:
        文件内容（Markdown格式）或错误信息
    """
    try:
        if os.path.exists(file_name):
            path = Path(file_name)
        else:
            path = Path("output").joinpath(file_name)
        
        if not path.exists():
            raise FileNotFoundError(f"Could not find file: {path}")
        
        converter = MarkdownConverter()
        return converter.convert(str(path)).text_content
    except Exception as e:
        return f"Error reading file: {e}"

@tool  
def list_files(dir_path: str = "") -> str:
    """列出目录中的文件
    
    Args:
        dir_path: 目录路径，默认为output目录
        
    Returns:
        文件列表的JSON字符串或错误信息
    """
    try:
        if dir_path:
            data_dir = Path(dir_path)
        else:
            data_dir = Path("output")
        
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            return json.dumps([], indent=2, ensure_ascii=False)
        
        file_list = [str(file_path) for file_path in data_dir.iterdir()]
        return json.dumps(file_list, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error reading files: {e}"

@tool
def read_files(dir_path: str = "") -> str:
    """读取目录中所有文件的内容
    
    Args:
        dir_path: 目录路径，默认为output目录
        
    Returns:
        所有文件内容的JSON字符串或错误信息  
    """
    try:
        if dir_path:
            data_dir = Path(dir_path)
        else:
            data_dir = Path("output")
        
        if not data_dir.exists():
            return json.dumps([], indent=2, ensure_ascii=False)
        
        all_contents = []
        for file_path in data_dir.iterdir():
            if file_path.is_file():
                try:
                    converter = MarkdownConverter()
                    contents = converter.convert(str(file_path)).text_content
                    all_contents.append(f"Contents of {file_path.name}:\n{contents}")
                except Exception as e:
                    all_contents.append(f"Error reading {file_path.name}: {e}")
        
        return json.dumps(all_contents, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error reading files: {e}"
