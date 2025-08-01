"""测试和其他任务示例"""
from crawler import run_crawler

def test_basic_crawl():
    """测试基本爬虫功能"""
    task = "搜索'python编程教程'，读取第一个结果，并保存为python_tutorial.md"
    run_crawler(task)

def test_36kr_crawl():
    """测试36kr爬虫"""
    task = """
从36kr创投平台抓取初创企业融资信息:
1. 搜索36kr创投或融资相关内容
2. 读取找到的URL内容
3. 保存原始内容为36kr_raw.md
4. 分析并提取融资信息(公司名、融资金额、轮次、时间)
5. 生成结构化报告保存为36kr_report.md
"""
    run_crawler(task)

def custom_task():
    """自定义任务"""
    print("请输入你的爬虫任务:")
    task = input()
    run_crawler(task)

if __name__ == "__main__":
    print("选择测试:")
    print("1. 基本爬虫测试")
    print("2. 36kr爬虫测试") 
    print("3. 自定义任务")
    
    choice = input("请选择 (1-3): ")
    
    if choice == "1":
        test_basic_crawl()
    elif choice == "2":
        test_36kr_crawl()
    elif choice == "3":
        custom_task()
    else:
        print("无效选择")
