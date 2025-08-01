"""简化的LangGraph爬虫工作流"""
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
# 导入与原版一致的工具函数

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# 加载环境变量
load_dotenv()
from file_tool import save_file, read_file, list_files, read_files
from jina_tool import jina_url_reader, jina_search

class State(TypedDict):
    """简单的状态定义"""
    messages: Annotated[list[BaseMessage], add_messages]

# 初始化LLM
llm = ChatOpenAI(
    model="Qwen/Qwen3-8B",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url='https://api-inference.modelscope.cn/v1/',
    # api_key='ms-848fbf20-9a26-4490-8bc5-a87f7ccf7ddf', 
    temperature=0.7,
    max_tokens=2000
)

# 定义工具 - 使用与原版一致的函数名
tools = [save_file, read_file, list_files, read_files, jina_url_reader, jina_search]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """聊天机器人节点 - 添加结束逻辑"""
    response = llm_with_tools.invoke(state["messages"])
    
    # 检查是否应该结束对话
    if response.content and any(keyword in response.content.lower() for keyword in 
                               ["任务完成", "完成任务", "已完成", "结束", "finished", "done"]):
        # 如果AI表示任务完成，则不调用工具
        response.tool_calls = []
    
    return {"messages": [response]}
def should_continue(state: State):
    """决定是否继续执行或结束"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果有工具调用，继续执行工具
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # 如果没有工具调用，结束对话
    return "end"

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()

def run_crawler(task: str):
    """运行爬虫任务"""
    print(f"🚀 开始执行任务: {task}")
    
    messages = [{"role": "user", "content": task}]
    
    for event in graph.stream({"messages": messages}):
        for value in event.values():
            if "messages" in value and value["messages"]:
                message = value["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    print(f"🤖 AI: {message.content}")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        print(f"🔧 调用工具: {tool_call['name']}")
                        # 1. 使用jina_search搜索"36kr创投融资"
if __name__ == "__main__":
    # 36kr爬虫任务 - 使用简化的搜索查询
    task = """
从36kr创投平台抓取初创企业融资信息:

可用工具：
- jina_search: 搜索网页内容
- jina_url_reader: 读取指定URL的内容（自动保存文件）
- save_file: 保存内容到文件
- read_file: 读取文件内容
- list_files: 列出文件
- read_files: 读取目录中所有文件

任务流程：
1. 使用jina_search搜索"36kr创投平台"
2. 从搜索结果中找到36kr相关页面的URL
3. 使用jina_url_reader读取URL内容（会自动保存）
4. 使用read_file读取保存的文件
5. 分析内容，提取最近的融资信息（公司名、融资金额、轮次、时间）
6. 使用save_file保存分析结果为36kr_finance_report.md

重要提示：
1. 完成所有步骤后，请明确说明"任务完成"
2. 不要重复执行相同的操作
"""   
    run_crawler(task)
