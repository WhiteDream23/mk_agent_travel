"""
MovieCompanion主程序 - 集成向量数据库版本
"""

from movie_agent import get_smart_response, smart_agent
import uuid

def main():
    print("🎬 MovieCompanion - 智能电影推荐助手 (Milvus向量数据库版)")
    print("=" * 65)
    print("✨ 功能：智能电影推荐 + 实时数据获取 + Milvus向量分析")
    print("🧠 新特性：基于Milvus的高性能向量检索和个性化推荐")
    print("=" * 65)
    
    # 显示数据库统计信息
    try:
        stats = smart_agent.get_database_stats()
        print(f"📊 Milvus数据库状态：")
        print(f"   - 电影数量：{stats.get('movies_count', 0)} 部")
        print(f"   - 用户数量：{stats.get('users_count', 0)} 人")
        print(f"   - AI模型：{stats.get('model_name', 'Unknown')}")
        print(f"   - 服务器：{stats.get('host', 'localhost')}:{stats.get('port', '19530')}")
        print(f"   - 向量维度：{stats.get('vector_dim', 384)}维")
        print("=" * 65)
    except Exception as e:
        print(f"⚠️ Milvus数据库状态检查失败：{e}")
        print("💡 请确保Milvus服务器正在运行")
        print("🚀 启动Milvus: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest standalone")
        print("=" * 65)
    
    print("💭 请告诉我您的观影需求或当前心情：")
    print("📝 示例：")
    print("   - '我心情不好，想看点治愈的电影'")
    print("   - '最近有什么好看的电影？'")
    print("   - '推荐一些和《肖申克的救赎》相似的电影'")
    print("⌨️  输入 'quit' 或 'exit' 退出")
    print("🔧 输入 'stats' 查看Milvus数据库统计信息")
    print("-" * 65)
    
    # 生成用户ID（简单演示）
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    print(f"👤 您的会话ID：{user_id}")
    print("-" * 65)
    
    while True:
        try:
            user_input = input("👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢使用MovieCompanion，再见！")
                break
            
            if user_input.lower() == 'stats':
                try:
                    stats = smart_agent.get_database_stats()
                    print("📊 **Milvus数据库统计信息：**")
                    print(f"   🎬 电影总数：{stats.get('movies_count', 0)} 部")
                    print(f"   👥 用户总数：{stats.get('users_count', 0)} 人")
                    print(f"   🤖 AI模型：{stats.get('model_name', 'Unknown')}")
                    print(f"   �️ 服务器：{stats.get('host', 'localhost')}:{stats.get('port', '19530')}")
                    print(f"   📐 向量维度：{stats.get('vector_dim', 384)}维")
                    
                    # 测试搜索功能
                    if stats.get('movies_count', 0) > 0:
                        print("\n🔍 **测试Milvus向量搜索：**")
                        test_movies = smart_agent.search_similar_movies_by_title("肖申克的救赎", 3)
                        if test_movies:
                            for i, movie in enumerate(test_movies, 1):
                                print(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
                        else:
                            print("   暂无搜索结果")
                except Exception as e:
                    print(f"❌ 获取统计信息失败：{e}")
                print("-" * 65)
                continue
            
            if not user_input:
                continue
            
            print("🤖 正在分析并为您推荐...")
            response = get_smart_response(user_input, user_id)
            print(f"🎬 推荐助手:\n{response}")
            print("-" * 65)
            
        except KeyboardInterrupt:
            print("\n👋 感谢使用MovieCompanion，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误：{e}")
            print("请重新输入您的需求。")

if __name__ == "__main__":
    main()
