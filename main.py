"""
简化版MovieCompanion主程序
"""

from movie_agent import get_simple_response

def main():
    print("🎬 MovieCompanion - 简化版电影推荐助手")
    print("=" * 50)
    print("✨ 功能：智能电影推荐 + 实时数据获取")
    print("=" * 50)
    print("💭 请告诉我您的观影需求或当前心情：")
    print("📝 示例：'我心情不好，想看点治愈的电影' 或 '最近有什么好看的电影？'")
    print("⌨️  输入 'quit' 或 'exit' 退出")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢使用MovieCompanion，再见！")
                break
            
            if not user_input:
                continue
            
            print("🤖 正在为您推荐...")
            response = get_simple_response(user_input)
            print(f"🎬 推荐助手:\n{response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 感谢使用MovieCompanion，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误：{e}")
            print("请重新输入您的需求。")

if __name__ == "__main__":
    main()
