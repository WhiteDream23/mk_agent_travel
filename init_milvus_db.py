"""
Milvus向量数据库初始化脚本
用于首次设置和数据导入
"""

import os
import sys
import requests
import json
from milvus_db import get_milvus_db, init_milvus_db_with_sample_data
from agents.movie_database_agent import MOVIE_DATABASE
from agents.realtime_movie_agent import RealTimeMovieDataAgent
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_milvus_server():
    """检查Milvus服务器是否运行"""
    try:
        from pymilvus import connections, utility
        connections.connect(host="localhost", port="19530")
        logger.info("✅ Milvus服务器运行正常")
        return True
    except Exception as e:
        logger.error(f"❌ 无法连接到Milvus服务器：{e}")
        logger.info("💡 请启动Milvus服务器:")
        logger.info("🐳 Docker方式: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest standalone")
        logger.info("📁 或下载并运行Milvus standalone版本")
        return False

def init_database():
    """初始化Milvus数据库"""
    logger.info("🚀 开始初始化Milvus向量数据库...")
    
    # 检查Milvus服务器
    if not check_milvus_server():
        return None
    
    # 获取Milvus数据库实例
    try:
        milvus_db = get_milvus_db()
    except Exception as e:
        logger.error(f"❌ 初始化Milvus数据库失败：{e}")
        return None
    
    # 检查是否已有数据
    stats = milvus_db.get_database_stats()
    logger.info(f"📊 当前数据库状态：{stats.get('movies_count', 0)} 部电影，{stats.get('users_count', 0)} 个用户")
    
    if stats.get('movies_count', 0) > 0:
        logger.info("✅ 数据库已有数据，无需重新初始化")
        return milvus_db
    
    # 1. 添加本地电影数据
    logger.info("\n📚 正在添加本地电影数据...")
    local_movies = []
    movie_id = 1
    
    for mood, movies in MOVIE_DATABASE.items():
        for movie in movies:
            movie_with_id = movie.copy()
            movie_with_id['id'] = f"local_{movie_id}"
            movie_with_id['mood_tag'] = mood
            if 'tags' in movie_with_id:
                movie_with_id['genres'] = movie_with_id['tags']
            local_movies.append(movie_with_id)
            movie_id += 1
    
    try:
        milvus_db.batch_add_movies(local_movies)
        logger.info(f"✅ 已添加 {len(local_movies)} 部本地电影")
    except Exception as e:
        logger.error(f"❌ 添加本地电影失败：{e}")
        return None
    
    # 2. 尝试添加实时电影数据
    logger.info("\n🌐 正在获取实时电影数据...")
    try:
        realtime_agent = RealTimeMovieDataAgent()
        now_playing = realtime_agent.get_now_playing_movies()
        
        if now_playing:
            if isinstance(now_playing, str):
                movies_data = json.loads(now_playing)
            else:
                movies_data = now_playing
            
            # 处理TMDB数据
            processed_movies = []
            for movie in movies_data[:20]:  # 限制数量
                if movie.get('title') and movie.get('overview'):
                    processed_movie = {
                        'id': f"tmdb_{movie.get('id', movie['title'])}",
                        'title': movie['title'],
                        'overview': movie['overview'],
                        'rating': movie.get('vote_average', 0),
                        'release_date': movie.get('release_date', ''),
                        'genres': [],  # TMDB需要额外API调用获取类型名称
                        'popularity': movie.get('popularity', 0),
                        'director': 'Unknown'  # TMDB需要额外API调用获取导演
                    }
                    processed_movies.append(processed_movie)
            
            if processed_movies:
                milvus_db.batch_add_movies(processed_movies)
                logger.info(f"✅ 已添加 {len(processed_movies)} 部实时电影")
            else:
                logger.warning("⚠️ 没有找到有效的实时电影数据")
        else:
            logger.warning("⚠️ 无法获取实时电影数据")
    
    except Exception as e:
        logger.warning(f"⚠️ 获取实时数据失败：{e}")
        logger.info("继续使用本地数据...")
    
    # 3. 创建示例用户偏好
    logger.info("\n👤 正在创建示例用户偏好...")
    sample_users = [
        {
            'user_id': 'demo_user_1',
            'preferences': {
                'favorite_genres': ['科幻', '动作', '悬疑'],
                'mood_preferences': ['刺激', '紧张'],
                'rating_range': [7.0, 10.0]
            }
        },
        {
            'user_id': 'demo_user_2',
            'preferences': {
                'favorite_genres': ['治愈', '爱情', '喜剧'],
                'mood_preferences': ['温暖', '轻松'],
                'rating_range': [6.0, 10.0]
            }
        },
        {
            'user_id': 'demo_user_3',
            'preferences': {
                'favorite_genres': ['动画', '奇幻', '冒险'],
                'mood_preferences': ['想象力', '童真'],
                'rating_range': [7.5, 10.0]
            }
        }
    ]
    
    for user_data in sample_users:
        try:
            milvus_db.add_user_preference(user_data['user_id'], user_data['preferences'])
        except Exception as e:
            logger.error(f"添加用户 {user_data['user_id']} 失败：{e}")
    
    logger.info(f"✅ 已创建 {len(sample_users)} 个示例用户")
    
    # 4. 最终统计
    final_stats = milvus_db.get_database_stats()
    logger.info(f"\n🎉 Milvus数据库初始化完成！")
    logger.info(f"📊 最终统计：{final_stats.get('movies_count', 0)} 部电影，{final_stats.get('users_count', 0)} 个用户")
    logger.info(f"🤖 AI模型：{final_stats.get('model_name', 'Unknown')}")
    logger.info(f"🖥️ 服务器：{final_stats.get('host', 'localhost')}:{final_stats.get('port', '19530')}")
    logger.info(f"📐 向量维度：{final_stats.get('vector_dim', 384)}维")
    
    return milvus_db

def test_milvus_search():
    """测试Milvus向量搜索功能"""
    logger.info("\n🔍 测试Milvus向量搜索功能...")
    
    if not check_milvus_server():
        return
    
    try:
        milvus_db = get_milvus_db()
        
        # 测试文本搜索
        logger.info("\n1. 测试情绪搜索：")
        results = milvus_db.search_similar_movies("我感到孤独，需要治愈", n_results=3)
        for i, movie in enumerate(results, 1):
            logger.info(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
        
        # 测试电影相似性搜索
        logger.info("\n2. 测试电影相似性搜索：")
        results = milvus_db.search_similar_movies("科幻 动作 未来", n_results=3)
        for i, movie in enumerate(results, 1):
            logger.info(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
        
        # 测试用户个性化推荐
        logger.info("\n3. 测试个性化推荐：")
        results = milvus_db.get_personalized_recommendations("demo_user_1", n_results=3)
        for i, movie in enumerate(results, 1):
            logger.info(f"   {i}. 《{movie['title']}》- 评分：{movie['rating']}")
        
        # 测试电影ID相似性搜索
        if results:
            logger.info("\n4. 测试基于电影ID的相似性搜索：")
            first_movie_id = results[0]['id']
            similar_results = milvus_db.search_similar_movies(movie_id=first_movie_id, n_results=3)
            for i, movie in enumerate(similar_results, 1):
                logger.info(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
    
    except Exception as e:
        logger.error(f"❌ 测试搜索功能失败：{e}")

def show_database_status():
    """显示数据库状态"""
    if not check_milvus_server():
        return
    
    try:
        milvus_db = get_milvus_db()
        stats = milvus_db.get_database_stats()
        
        logger.info(f"\n📊 Milvus数据库状态：")
        logger.info(f"   🎬 电影数量：{stats.get('movies_count', 0)} 部")
        logger.info(f"   👥 用户数量：{stats.get('users_count', 0)} 人")
        logger.info(f"   🤖 AI模型：{stats.get('model_name', 'Unknown')}")
        logger.info(f"   🖥️ 服务器：{stats.get('host', 'localhost')}:{stats.get('port', '19530')}")
        logger.info(f"   📐 向量维度：{stats.get('vector_dim', 384)}维")
        
        # 检查集合状态
        from pymilvus import utility
        movie_collection_exists = utility.has_collection("movie_collection")
        user_collection_exists = utility.has_collection("user_collection")
        
        logger.info(f"\n📚 集合状态：")
        logger.info(f"   🎬 电影集合：{'✅ 存在' if movie_collection_exists else '❌ 不存在'}")
        logger.info(f"   👥 用户集合：{'✅ 存在' if user_collection_exists else '❌ 不存在'}")
        
    except Exception as e:
        logger.error(f"❌ 获取数据库状态失败：{e}")

def main():
    """主函数"""
    print("🎬 MovieCompanion Milvus向量数据库管理工具")
    print("=" * 55)
    
    choice = input("""请选择操作：
1. 检查Milvus服务器状态
2. 初始化数据库
3. 测试搜索功能
4. 查看数据库状态
5. 完整初始化并测试

请输入选项 (1-5): """)
    
    if choice == "1":
        check_milvus_server()
    
    elif choice == "2":
        init_database()
    
    elif choice == "3":
        test_milvus_search()
    
    elif choice == "4":
        show_database_status()
    
    elif choice == "5":
        # 完整流程
        if check_milvus_server():
            db = init_database()
            if db:
                logger.info("\n" + "="*50)
                test_milvus_search()
                logger.info("\n" + "="*50)
                show_database_status()
    
    else:
        logger.error("❌ 无效选项")

if __name__ == "__main__":
    main()
