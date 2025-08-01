# LangGraph网页爬虫

一个使用LangGraph框架重新实现的网页爬虫工具，与原agentica版本**完全兼容**。

## 🎯 工具对应关系

### FileTool -> LangGraph版本
| 原版函数 | LangGraph版本 | 功能说明 |
|---------|---------------|----------|
| `save_file(contents, file_name, overwrite, save_dir)` | ✅ 完全一致 | 保存文件 |
| `read_file(file_name)` | ✅ 完全一致 | 读取文件并转换为Markdown |
| `list_files(dir_path)` | ✅ 完全一致 | 列出目录文件（JSON格式） |
| `read_files(dir_path)` | ✅ 完全一致 | 读取目录中所有文件 |

### JinaTool -> LangGraph版本  
| 原版函数 | LangGraph版本 | 功能说明 |
|---------|---------------|----------|
| `jina_url_reader(url)` | ✅ 完全一致 | 读取URL并自动保存文件 |
| `jina_search(query)` | ✅ 完全一致 | 搜索并自动保存文件 |

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑.env文件，填入API密钥
```

### 3. 运行爬虫
```bash
# 直接运行36kr示例
python crawler.py

# 运行一致性测试
python test_consistency.py

# 运行交互测试
python test.py
```

## 文件说明

- `crawler.py` - 主要的LangGraph爬虫工作流
- `file_tool.py` - 文件操作工具（与原FileTool完全一致）
- `jina_tool.py` - 网页抓取工具（与原JinaTool完全一致）
- `test.py` - 交互测试和示例
- `test_consistency.py` - 工具一致性验证

## 核心特性

### 🔄 完全兼容
- **函数签名**: 与原版参数完全一致
- **返回格式**: 保持相同的返回值格式
- **文件处理**: 相同的Markdown转换和自动保存逻辑
- **错误处理**: 相同的错误信息格式

### 🚀 LangGraph增强
- **智能编排**: AI自动决定工具调用顺序
- **状态管理**: 工作流状态跟踪
- **流式处理**: 实时查看处理过程
- **异常恢复**: 更好的错误恢复机制

## 使用示例

### 基本用法（与原版相同）
```python
# 文件操作
save_file("内容", "文件名.txt")
content = read_file("文件名.txt")  # 返回Markdown格式
files = list_files()              # 返回JSON格式
all_content = read_files()        # 返回JSON格式

# 网页抓取
search_result = jina_search("查询内容")     # 自动保存文件
url_content = jina_url_reader("网址")       # 自动保存文件
```

### LangGraph工作流
```python
from crawler import run_crawler

task = """
使用jina_search搜索内容，
然后用jina_url_reader读取URL，
最后用save_file保存结果
"""
run_crawler(task)
```

## 优势对比

| 特性 | 原agentica版本 | LangGraph版本 |
|------|---------------|---------------|
| **工具兼容性** | ✅ 原版 | ✅ 100%兼容 |
| **智能编排** | ❌ 手动调用 | ✅ AI自动编排 |
| **状态管理** | ❌ 无状态 | ✅ 完整状态跟踪 |
| **流程可视** | ❌ 不支持 | ✅ 可生成流程图 |
| **错误恢复** | ⚠️ 基础 | ✅ 智能恢复 |
| **扩展性** | ⚠️ 中等 | ✅ 高度可扩展 |

使用LangGraph版本，你可以获得原版的所有功能，同时享受AI编排的智能化优势！🎉
