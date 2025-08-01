"""简单的工具功能测试"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_crawler_workflow():
    """测试爬虫工作流"""
    print("🧪 测试LangGraph爬虫工作流...")
    
    try:
        from crawler import run_crawler
        
        # 简单的文件操作测试
        simple_task = """
请执行以下简单任务来测试工具：
1. 使用save_file保存一段文本到test_file.txt
2. 使用read_file读取刚才保存的文件
3. 使用list_files列出当前目录的文件
"""
        
        print("🚀 开始执行简单测试任务...")
        run_crawler(simple_task)
        
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_search_only():
    """只测试搜索功能"""
    print("\n🧪 测试搜索功能...")
    
    try:
        from crawler import run_crawler
        
        search_task = """
请使用jina_search从36kr创投平台抓取初创企业融资信息，并将搜索结果保存为search_result.md文件。
"""
        
        print("🔍 开始执行搜索测试...")
        run_crawler(search_task)
        
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
        import traceback
        traceback.print_exc()

def check_api_keys():
    """检查API密钥配置"""
    print("🔑 检查API密钥配置...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    jina_key = os.getenv("JINA_API_KEY")
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {'*' * 10}{openai_key[-4:] if len(openai_key) > 4 else '****'}")
    else:
        print("❌ OPENAI_API_KEY 未设置")
        
    if jina_key:
        print(f"✅ JINA_API_KEY: {'*' * 10}{jina_key[-4:] if len(jina_key) > 4 else '****'}")
    else:
        print("⚠️ JINA_API_KEY 未设置（可选）")

if __name__ == "__main__":
    print("🧪 LangGraph爬虫功能测试")
    print("=" * 50)
    
    # 检查配置
    check_api_keys()
    
    print("\n选择测试:")
    print("1. 简单工具测试")
    print("2. 搜索功能测试") 
    print("3. 退出")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            test_crawler_workflow()
        elif choice == "2":
            test_search_only()
        elif choice == "3":
            print("👋 退出测试")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出测试")
    except Exception as e:
        print(f"❌ 测试程序出错: {e}")
    
    print("\n🏁 测试结束")
