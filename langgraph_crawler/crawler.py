"""简化的LangGraph爬虫工作流"""
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
# 导入与原版一致的工具函数

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
# from langchain_community.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# 加载环境变量
load_dotenv()
from file_tool import save_file, read_file, list_files, read_files
from jina_tool import jina_url_reader, jina_search
from free_web_tool import free_url_reader, free_search
from time_tool import get_current_time, get_time_info

class State(TypedDict):
    """简单的状态定义"""
    messages: Annotated[list[BaseMessage], add_messages]

# 初始化LLM
llm = ChatOpenAI(
    # model="Qwen/Qwen3-14B",
    # model='Qwen/Qwen2.5-14B-Instruct',
    model='Qwen/Qwen3-30B-A3B-Instruct-2507',
    # base_url="https://api.siliconflow.cn/v1",
    # api_key=os.getenv("OPENAI_API_KEY"),

    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-a0ff81a2-f678-40ca-9932-1279430f8d5e',
    temperature=0.0,
    max_tokens=2000,
    # streaming=False,
    extra_body={
        "enable_thinking": False,
    }
)

# 定义工具 - 使用与原版一致的函数名，加上免费替代工具和时间工具
tools = [save_file, read_file, list_files, read_files, free_url_reader, free_search, get_current_time, get_time_info]
# tools = [save_file, read_file, list_files, read_files, free_url_reader, free_search]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """聊天机器人节点 - 添加结束逻辑和上下文管理"""
    messages = state["messages"]
    
    # 上下文管理：如果消息过多，保留最新的几条
    # if len(messages) > 10:
    #     # 保留用户的初始任务和最近的5轮对话
    #     initial_message = messages[0]  # 用户的初始任务
    #     recent_messages = messages[-8:]  # 最近的8条消息（约4轮对话）
    #     managed_messages = [initial_message] + recent_messages
    #     print(f"📝 上下文管理：保留 {len(managed_messages)} 条消息（原 {len(messages)} 条）")
    # else:
    #     managed_messages = messages
    
    # response = llm_with_tools.invoke(managed_messages)
    response = llm_with_tools.invoke(messages)

    # 检查是否应该结束对话
    if response.content and any(keyword in response.content.lower() for keyword in 
                               ["任务完成", "完成任务", "已完成", "结束", "finished", "done"]):
        # 如果AI表示任务完成，则不调用工具
        response.tool_calls = []
        print("🎯 AI表示任务完成，准备结束对话")
    
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

graph_builder.add_edge("tools", "chatbot")  # 修复：工具执行后回到chatbot
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()

def save_graph_visualization():
    """生成并保存LangGraph的可视化图形"""
    try:
        # 尝试生成Mermaid图并保存为PNG
        png_data = graph.get_graph().draw_mermaid_png()
        with open("langgraph_structure.png", "wb") as f:
            f.write(png_data)
        print("✅ 图形结构已保存为 'langgraph_structure.png'")
        
        # 如果在Jupyter环境中，尝试显示图片
        try:
            try:
                from IPython.display import Image, display
                display(Image(png_data))
                print("✅ 图形结构已在notebook中显示")
            except ImportError:
                print("💡 未检测到IPython，图片已保存到文件")
        except Exception as e:
            print(f"💡 在普通Python环境中运行，图片已保存到文件，错误信息: {e}")
            
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("💡 请安装: pip install pygraphviz 或 pip install graphviz")
    except Exception as e:
        print(f"❌ 生成图形时出错: {e}")
        print("💡 如果您想查看图形结构，请确保安装了graphviz相关依赖")

# 尝试生成图形
print("🔄 正在生成LangGraph结构图...")
save_graph_visualization()


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

def run_crawler_debug(task: str):
    """调试版爬虫任务执行器"""
    print(f"🚀 开始执行任务: {task}")
    
    messages = [{"role": "user", "content": task}]
    step_count = 0
    
    for event in graph.stream({"messages": messages}):
        step_count += 1
        print(f"\n{'='*50}")
        print(f"📍 执行步骤 {step_count}")
        print(f"{'='*50}")
        
        for node_name, value in event.items():
            print(f"🏃 当前节点: {node_name}")
            
            if "messages" in value and value["messages"]:
                message = value["messages"][-1]
                
                # 显示AI的文本回复
                if hasattr(message, 'content') and message.content:
                    print(f"🤖 AI: {message.content}")
                
                # 详细显示工具调用
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print(f"\n🔧 计划调用的工具:")
                    for i, tool_call in enumerate(message.tool_calls, 1):
                        tool_name = tool_call.get('name', 'unknown')
                        tool_args = tool_call.get('args', {})
                        print(f"  {i}. {tool_name}")
                        print(f"     参数: {tool_args}")
                
                # 显示工具执行结果
                if hasattr(message, 'tool_call_id'):
                    print(f"✅ 工具执行完成: {message.name if hasattr(message, 'name') else 'unknown'}")
            
            # 检查是否是工具节点的输出
            if node_name == "tools" and "messages" in value:
                tool_messages = value["messages"]
                for tool_msg in tool_messages:
                    if hasattr(tool_msg, 'name'):
                        print(f"🛠️ 工具 {tool_msg.name} 执行完成")
                        if hasattr(tool_msg, 'content'):
                            print(f"    结果: {tool_msg.content[:100]}...")


if __name__ == "__main__":
    # 36kr爬虫任务 - 使用免费工具替代
    task = """
从36kr创投平台https://pitchhub.36kr.com/financing-flash抓取所有初创企业融资的信息;
下面是一个大致流程, 你根据每一步的运行结果对当前计划中的任务做出适当调整:
- 爬取并保存url内容，保存为36kr_finance_date.md文件, date是当前日期;
- 理解md文件，筛选最近3天的初创企业融资快讯, 打印前5个，需要提取快讯的核心信息，包括标题、链接、时间、融资规模、融资阶段等;
- 将全部结果使用自然语言存在本地search_result_date.md中,date是当前日期;
"""   
    run_crawler(task)
    # run_crawler_debug(task)
