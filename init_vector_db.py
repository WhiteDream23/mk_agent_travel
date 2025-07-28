"""
向量数据库初始化脚本
用于首次设置和数据导入
"""

import os
import sys
import requests
import json
from vector_db import get_vector_db
from agents.movie_database_agent import MOVIE_DATABASE
from agents.realtime_movie_agent import RealTimeMovieDataAgent

def init_database():
    """初始化向量数据库"""
    print("🚀 开始初始化向量数据库...")
    
    # 获取向量数据库实例
    vector_db = get_vector_db()
    
    # 检查是否已有数据
    stats = vector_db.get_database_stats()
    print(f"📊 当前数据库状态：{stats['movies_count']} 部电影，{stats['users_count']} 个用户")
    
    if stats['movies_count'] > 0:
        print("✅ 数据库已有数据，无需重新初始化")
        return vector_db
    
    # 1. 添加本地电影数据
    print("\n📚 正在添加本地电影数据...")
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
    
    vector_db.batch_add_movies(local_movies)
    print(f"✅ 已添加 {len(local_movies)} 部本地电影")
    
    # 2. 尝试添加实时电影数据
    print("\n🌐 正在获取实时电影数据...")
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
                vector_db.batch_add_movies(processed_movies)
                print(f"✅ 已添加 {len(processed_movies)} 部实时电影")
            else:
                print("⚠️ 没有找到有效的实时电影数据")
        else:
            print("⚠️ 无法获取实时电影数据")
    
    except Exception as e:
        print(f"⚠️ 获取实时数据失败：{e}")
        print("继续使用本地数据...")
    
    # 3. 创建示例用户偏好
    print("\n👤 正在创建示例用户偏好...")
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
        }
    ]
    
    for user_data in sample_users:
        vector_db.add_user_preference(user_data['user_id'], user_data['preferences'])
    
    print(f"✅ 已创建 {len(sample_users)} 个示例用户")
    
    # 4. 最终统计
    final_stats = vector_db.get_database_stats()
    print(f"\n🎉 数据库初始化完成！")
    print(f"📊 最终统计：{final_stats['movies_count']} 部电影，{final_stats['users_count']} 个用户")
    print(f"🤖 AI模型：{final_stats['model_name']}")
    print(f"💾 数据库位置：{final_stats['db_path']}")
    
    return vector_db

def test_vector_search():
    """测试向量搜索功能"""
    print("\n🔍 测试向量搜索功能...")
    
    vector_db = get_vector_db()
    
    # 测试文本搜索
    print("\n1. 测试情绪搜索：")
    results = vector_db.search_similar_movies("我感到孤独，需要治愈", n_results=3)
    for i, movie in enumerate(results, 1):
        print(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
    
    # 测试电影相似性搜索
    print("\n2. 测试电影相似性搜索：")
    results = vector_db.search_similar_movies("科幻 动作 未来", n_results=3)
    for i, movie in enumerate(results, 1):
        print(f"   {i}. 《{movie['title']}》- 相似度：{movie['similarity']:.2%}")
    
    # 测试用户个性化推荐
    print("\n3. 测试个性化推荐：")
    results = vector_db.get_personalized_recommendations("demo_user_1", n_results=3)
    for i, movie in enumerate(results, 1):
        print(f"   {i}. 《{movie['title']}》- 评分：{movie['rating']}")

def main():
    """主函数"""
    print("🎬 MovieCompanion 向量数据库初始化工具")
    print("=" * 50)
    
    choice = input("请选择操作：\n1. 初始化数据库\n2. 测试搜索功能\n3. 查看数据库状态\n请输入选项 (1-3): ")
    
    if choice == "1":
        init_database()
        print("\n是否要测试搜索功能？(y/n): ", end="")
        if input().lower() == 'y':
            test_vector_search()
    
    elif choice == "2":
        test_vector_search()
    
    elif choice == "3":
        vector_db = get_vector_db()
        stats = vector_db.get_database_stats()
        print(f"\n📊 数据库状态：")
        print(f"   🎬 电影数量：{stats['movies_count']} 部")
        print(f"   👥 用户数量：{stats['users_count']} 人")
        print(f"   🤖 AI模型：{stats['model_name']}")
        print(f"   💾 数据库路径：{stats['db_path']}")
    
    else:
        print("❌ 无效选项")

if __name__ == "__main__":
    main()
