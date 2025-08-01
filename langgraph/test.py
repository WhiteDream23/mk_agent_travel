from typing import Annotated
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# 加载 .env 文件
load_dotenv()

# 修改API密钥配置，支持多种API
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key and not openai_api_key:
    raise ValueError("请在 .env 文件中设置 GEMINI_API_KEY 或 OPENAI_API_KEY")

# 根据可用的API密钥选择模型
if gemini_api_key:
    
    llm = ChatOpenAI(
        model="gemini-2.5-flash",
       base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=gemini_api_key,
        temperature=0.7,
        max_tokens=2000
    )
    print("✅ 使用 Google Gemini API")
    
elif openai_api_key:

    
    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        base_url="https://api.siliconflow.cn/v1",
        api_key=openai_api_key,
        temperature=0.7,
        max_tokens=2000
    )
    print("✅ 使用硅基流动 API")



from langchain_openai import ChatOpenAI
from typing import Annotated

# 尝试导入TavilySearch，如果失败则使用备用方案
try:
    from langchain_tavily import TavilySearch
    TAVILY_AVAILABLE = True
except ImportError:
    print("⚠️  TavilySearch未安装，将使用无工具模式")
    print("💡 如需搜索功能，请运行: pip install langchain-tavily-search")
    TAVILY_AVAILABLE = False

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from langchain_core.tools import tool,InjectedToolCallId
# 条件导入LangGraph预构建工具
if TAVILY_AVAILABLE:
    from langgraph.prebuilt import ToolNode, tools_condition



class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

graph_builder = StateGraph(State)

# 根据是否有Tavily来配置工具
if TAVILY_AVAILABLE:
    try:
        # tool = TavilySearch(max_results=2)
        # tools = [tool]
        @tool
        def human_assistance(
            name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
        ) -> str:
            """Request assistance from a human."""
            human_response = interrupt(
                {
                    "question": "Is this correct?",
                    "name": name,
                    "birthday": birthday,
                },
            )
            # If the information is correct, update the state as-is.
            if human_response.get("correct", "").lower().startswith("y"):
                verified_name = name
                verified_birthday = birthday
                response = "Correct"
            # Otherwise, receive information from the human reviewer.
            else:
                verified_name = human_response.get("name", name)
                verified_birthday = human_response.get("birthday", birthday)
                response = f"Made a correction: {human_response}"

            # This time we explicitly update the state with a ToolMessage inside
            # the tool.
            state_update = {
                "name": verified_name,
                "birthday": verified_birthday,
                "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
            }
            # We return a Command object in the tool to update our state.
            return Command(update=state_update)

        tool = TavilySearch(max_results=2)
        tools = [tool, human_assistance]
        llm_with_tools = llm.bind_tools(tools)
        print("✅ Tavily搜索工具已配置")
    except Exception as e:
        print(f"⚠️  Tavily配置失败: {e}")
        print("💡 请检查TAVILY_API_KEY环境变量")
        tools = []
        llm_with_tools = llm
else:
    tools = []
    llm_with_tools = llm

# def chatbot(state: State):
#     return {"messages": [llm_with_tools.invoke(state["messages"])]}
def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Because we will be interrupting during tool execution,
    # we disable parallel tool calling to avoid repeating any
    # tool invocations when we resume.
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}

graph_builder.add_node("chatbot", chatbot)

# 只有在有工具时才添加工具节点和相关边
if tools and TAVILY_AVAILABLE:
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")

graph_builder.add_edge(START, "chatbot")
# graph = graph_builder.compile()
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)
# 生成并保存图形结构
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
            from IPython.display import Image, display
            display(Image(png_data))
            print("✅ 图形结构已在notebook中显示")
        except:
            print("💡 在普通Python环境中运行，图片已保存到文件")
            
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("💡 请安装: pip install pygraphviz 或 pip install graphviz")
    except Exception as e:
        print(f"❌ 生成图形时出错: {e}")
        print("💡 如果您想查看图形结构，请确保安装了graphviz相关依赖")

# 尝试生成图形
print("🔄 正在生成LangGraph结构图...")
save_graph_visualization()



config = {"configurable": {"thread_id": "1"}}

def stream_graph_updates(user_input: str):
    """处理用户输入并支持人机协作"""
    try:
        # 发送用户消息到图形
        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="values",
        )
        
        for event in events:
            if "messages" in event and event["messages"]:
                event["messages"][-1].pretty_print()
                
    except Exception as e:
        print(f"❌ 处理消息时出错: {e}")

def handle_human_interruption():
    """处理人机协作中断"""
    try:
        # 获取当前状态，检查是否有中断
        snapshot = graph.get_state(config)
        
        if snapshot.next:
            print("\n🤝 AI正在请求人工协助...")
            
            # 显示中断的原因
            print("💭 AI需要您的帮助来回答用户的问题")
            
            # 获取人工输入
            human_input = input("\n👤 请提供帮助 (或输入 'skip' 跳过): ").strip()
            
            if human_input.lower() == 'skip':
                print("⏭️ 跳过人工协助")
                # 发送空响应继续
                resume_command = Command(resume={"data": "用户选择跳过人工协助"})
            else:
                # 发送人工响应
                resume_command = Command(resume={"data": human_input})
            
            print("🔄 继续处理...")
            events = graph.stream(resume_command, config, stream_mode="values")
            
            for event in events:
                if "messages" in event and event["messages"]:
                    event["messages"][-1].pretty_print()
            
            return True
            
    except Exception as e:
        print(f"❌ 处理人工协助时出错: {e}")
        # 尝试发送默认响应来恢复
        try:
            resume_command = Command(resume={"data": "抱歉，人工协助暂时不可用，请继续与AI对话"})
            events = graph.stream(resume_command, config, stream_mode="values")
            for event in events:
                if "messages" in event and event["messages"]:
                    event["messages"][-1].pretty_print()
        except:
            pass
        return False
    
    return False

print("🤖 人机协作聊天机器人已启动!")
print("💡 当AI需要帮助时，您可以提供人工协助")
print("📝 输入 'quit', 'exit' 或 'q' 退出程序\n")

while True:
    try:
        # 首先检查是否有待处理的人工协助请求
        try:
            snapshot = graph.get_state(config)
            if snapshot and snapshot.next:
                print("🔍 检测到待处理的人工协助请求...")
                if handle_human_interruption():
                    continue
        except Exception as check_error:
            # 如果检查状态失败，继续正常流程
            pass
            
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break
            
        if user_input.strip():  # 只处理非空输入
            stream_graph_updates(user_input)
            
            # 处理完用户消息后，检查是否需要人工协助
            try:
                while True:
                    snapshot = graph.get_state(config)
                    if snapshot and snapshot.next:
                        # 有待处理的中断，处理人工协助
                        if not handle_human_interruption():
                            break  # 用户选择跳过或处理完成
                    else:
                        break  # 没有更多中断需要处理
            except Exception as interrupt_error:
                print(f"⚠️ 处理中断时出错: {interrupt_error}")
        else:
            print("💡 请输入一些内容...")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        break
    except EOFError:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print("💡 请检查API密钥配置和网络连接")
