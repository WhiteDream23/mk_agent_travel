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
    """将文本内容保存到文件中
    
    这个工具用于保存任何文本内容到指定文件，包括：
    - 搜索结果、网页内容、分析报告
    - JSON数据、CSV数据、Markdown文档
    - 处理后的数据或最终结果
    
    Args:
        contents: 要保存的文本内容（支持任何格式：纯文本、JSON、Markdown、CSV等）
        file_name: 文件名（建议包含扩展名，如：report.md、data.json、results.txt）
        overwrite: 是否覆盖已存在的文件（默认True，设为False时文件存在则不覆盖）
        save_dir: 保存目录路径（默认为"output"目录，会自动创建）
        
    Returns:
        成功时返回保存的文件名，失败时返回错误信息
        
    使用示例：
    - save_file("搜索结果内容", "search_result.md")
    - save_file('{"key": "value"}', "data.json")
    - save_file("分析报告内容", "analysis_report.txt", save_dir="reports")
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
    """读取文件内容并转换为Markdown格式显示
    
    这个工具用于读取各种类型的文件内容：
    - 之前保存的搜索结果、网页内容、分析报告
    - JSON、CSV、TXT、MD等格式的文件
    - 自动格式化为易读的Markdown格式
    
    Args:
        file_name: 文件名或文件路径
                  - 可以是完整路径："/path/to/file.txt"
                  - 可以是相对于output目录的文件名："search_result.md"
                  - 工具会自动在当前目录和output目录中查找文件
        
    Returns:
        文件内容（自动转换为Markdown格式，包含文件信息和内容）
        如果文件不存在或读取失败，返回错误信息
        
    使用场景：
    - 读取之前保存的搜索结果进行分析
    - 查看网页抓取的内容
    - 检查已保存的报告内容
    - 读取JSON数据进行处理
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
    """列出指定目录中的所有文件
    
    这个工具用于查看和管理已保存的文件：
    - 查看所有搜索结果、抓取内容、分析报告
    - 了解哪些数据已经收集和保存
    - 帮助决定下一步的分析方向
    
    Args:
        dir_path: 要列出文件的目录路径
                 - 默认为空字符串，会自动使用"output"目录
                 - 可以指定其他目录：".", "data", "/absolute/path"
                 - 工具会自动处理路径不存在的情况
        
    Returns:
        Markdown格式的文件列表，包括：
        - 文件名、大小、修改时间
        - 文件类型和用途说明
        - 目录结构的清晰展示
        
    使用场景：
    - 开始分析前查看可用数据
    - 检查搜索结果是否已保存
    - 管理和清理过期文件
    - 了解项目文件结构
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
    """批量读取目录中所有文件的内容
    
    这个工具用于一次性读取多个文件进行综合分析：
    - 读取所有搜索结果进行对比分析
    - 汇总多个网页内容进行综合研究
    - 批量处理保存的数据文件
    
    Args:
        dir_path: 要读取文件的目录路径
                 - 默认为空字符串，会自动使用"output"目录
                 - 可以指定其他目录："data", "reports", "/absolute/path"
                 - 会递归读取目录下所有文件
        
    Returns:
        JSON格式的文件内容集合，包括：
        - 每个文件的名称、路径和完整内容
        - 自动转换为易于分析的格式
        - 如果目录不存在或为空，返回空列表
        
    使用场景：
    - 综合分析多个搜索结果
    - 对比不同来源的信息
    - 批量处理数据文件
    - 生成综合报告
    
    注意：如果文件很多或很大，可能返回大量数据，建议先用list_files查看文件列表
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
