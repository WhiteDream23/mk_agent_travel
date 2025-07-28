"""
智能电影推荐Agent - 集成向量数据库版本
"""

import os
from typing import Dict, List
import json
from agents.realtime_movie_agent import RealTimeMovieDataAgent
from agents.movie_database_agent import MOVIE_DATABASE
from milvus_db import get_milvus_db, init_milvus_db_with_sample_data

class SmartMovieAgent:
    def __init__(self):
        self.realtime_agent = RealTimeMovieDataAgent()
        
        # 初始化Milvus向量数据库
        print("🚀 正在初始化Milvus向量数据库...")
        self.milvus_db = init_milvus_db_with_sample_data()
        
        # 用户偏好缓存
        self.user_sessions = {}
        
    def chat(self, user_input: str, user_id: str = "default_user") -> str:
        """处理用户输入并返回推荐"""
        
        # 检查是否需要实时数据
        if any(keyword in user_input for keyword in ["最新", "热映", "正在上映", "最近", "院线"]):
            return self._get_realtime_recommendations(user_input, user_id)
        
        # 检查情绪关键词并使用向量检索
        mood = self._extract_mood(user_input)
        if mood:
            return self._get_vector_recommendations(mood, user_input, user_id)
        
        # 默认推荐
        return self._get_personalized_recommendations(user_id)
    
    def _get_realtime_recommendations(self, user_input: str, user_id: str) -> str:
        """获取实时电影推荐并更新向量数据库"""
        try:
            # 获取实时数据
            movies = self.realtime_agent.get_now_playing_movies()
            
            if movies:
                result = "🎬 **当前正在热映的电影推荐：**\n\n"
                
                # 解析数据
                if isinstance(movies, str):
                    movies_data = json.loads(movies)
                else:
                    movies_data = movies
                
                # 使用向量数据库增强推荐
                enhanced_recommendations = self._enhance_with_vector_search(
                    movies_data[:5], user_input, user_id
                )
                
                for i, movie in enumerate(enhanced_recommendations, 1):
                    title = movie.get('title', '未知电影')
                    rating = movie.get('vote_average', movie.get('rating', 0))
                    overview = movie.get('overview', '暂无简介')
                    release_date = movie.get('release_date', '未知')
                    similarity = movie.get('similarity_reason', '')
                    
                    result += f"{i}. **《{title}》**\n"
                    result += f"   - 评分：{rating}/10\n"
                    result += f"   - 上映日期：{release_date}\n"
                    result += f"   - 简介：{overview[:100]}...\n"
                    if similarity:
                        result += f"   - 推荐理由：{similarity}\n"
                    result += "\n"
                
                # 添加个性化建议
                mood = self._extract_mood(user_input)
                if mood:
                    result += self._get_mood_specific_advice(mood)
                
                # 批量添加新电影到向量数据库（后台）
                self._add_movies_to_vector_db_async(movies_data[:10])
                
                result += "🎫 您可以通过各大购票平台查看具体排片时间和购票信息。"
                return result
            else:
                return "抱歉，暂时无法获取最新的电影信息。让我为您推荐一些优质电影。\n\n" + self._get_vector_recommendations("治愈", user_input, user_id)
                
        except Exception as e:
            print(f"获取实时电影数据失败：{e}")
            return "抱歉，获取实时电影数据时出现问题。让我为您推荐一些优质电影。\n\n" + self._get_vector_recommendations("治愈", user_input, user_id)
    
    def _get_vector_recommendations(self, mood: str, user_input: str, user_id: str) -> str:
        """基于向量数据库的推荐"""
        
        # 更新用户偏好
        self._update_user_preferences(user_id, mood, user_input)
        
        # 构建查询文本
        query_text = f"情绪：{mood}，{user_input}"
        
        # 从Milvus数据库搜索
        similar_movies = self.milvus_db.search_similar_movies(
            query=query_text,
            n_results=6
        )
        
        if not similar_movies:
            # 降级到传统推荐
            return self._get_mood_based_recommendations(mood, user_input)
        
        result = f"🎭 **基于AI向量分析的{mood}情绪推荐：**\n\n"
        
        for i, movie in enumerate(similar_movies[:4], 1):
            title = movie.get('title', '')
            year = movie.get('year', '')
            director = movie.get('director', '')
            rating = movie.get('rating', 0)
            genres = movie.get('genre', [])
            similarity = movie.get('similarity', 0)
            
            result += f"{i}. **《{title}》** ({year})\n"
            result += f"   - 导演：{director}\n"
            result += f"   - 评分：{rating}/10\n"
            result += f"   - 类型：{', '.join(genres) if isinstance(genres, list) else genres}\n"
            result += f"   - 匹配度：{similarity:.2%}\n"
            result += f"   - 推荐理由：{self._get_vector_recommendation_reason(movie, mood, similarity)}\n\n"
        
        # 添加相似电影推荐
        if similar_movies:
            first_movie = similar_movies[0]
            related_movies = self.milvus_db.search_similar_movies(
                movie_id=first_movie['id'],
                n_results=3
            )
            
            if related_movies:
                result += "🔗 **您可能还喜欢的相似电影：**\n"
                for movie in related_movies[:2]:
                    result += f"- 《{movie['title']}》({movie['year']}) - 相似度：{movie['similarity']:.2%}\n"
                result += "\n"
        
        # 添加个性化建议
        result += self._get_mood_specific_advice(mood)
        
        return result
    
    def _get_personalized_recommendations(self, user_id: str) -> str:
        """获取个性化推荐"""
        
        # 尝试基于用户历史偏好推荐
        personalized = self.milvus_db.get_personalized_recommendations(
            user_id=user_id,
            n_results=5
        )
        
        if personalized:
            result = "🎯 **为您个性化推荐：**\n\n"
            
            for i, movie in enumerate(personalized[:4], 1):
                title = movie.get('title', '')
                year = movie.get('year', '')
                rating = movie.get('rating', 0)
                genres = movie.get('genre', [])
                
                result += f"{i}. **《{title}》** ({year})\n"
                result += f"   - 评分：{rating}/10\n"
                result += f"   - 类型：{', '.join(genres) if isinstance(genres, list) else genres}\n\n"
        else:
            # 降级到热门推荐
            popular_movies = self.milvus_db.get_popular_movies(n_results=5)
            result = "🔥 **热门电影推荐：**\n\n"
            
            for i, movie in enumerate(popular_movies[:4], 1):
                title = movie.get('title', '')
                year = movie.get('year', '')
                rating = movie.get('rating', 0)
                
                result += f"{i}. **《{title}》** ({year}) - 评分：{rating}/10\n"
        
        result += "\n💡 告诉我您的心情或喜好，我可以为您提供更精准的推荐！"
        return result
    
    def _enhance_with_vector_search(self, movies_data: List[Dict], user_input: str, user_id: str) -> List[Dict]:
        """使用向量搜索增强实时电影推荐"""
        
        enhanced_movies = []
        
        for movie in movies_data:
            # 为每部电影添加相似性分析
            movie_title = movie.get('title', '')
            movie_overview = movie.get('overview', '')
            
            # 在Milvus数据库中搜索相似电影
            search_text = f"{movie_title} {movie_overview}"
            similar = self.milvus_db.search_similar_movies(
                query=search_text,
                n_results=3
            )
            
            # 添加相似性推荐理由
            if similar:
                best_match = similar[0]
                similarity_reason = f"与您可能喜欢的《{best_match['title']}》类似，匹配度{best_match['similarity']:.1%}"
                movie['similarity_reason'] = similarity_reason
                movie['vector_similarity'] = best_match['similarity']
            else:
                movie['similarity_reason'] = "最新热映电影，值得关注"
                movie['vector_similarity'] = 0.5
            
            enhanced_movies.append(movie)
        
        # 按相似度重新排序
        enhanced_movies.sort(key=lambda x: x.get('vector_similarity', 0), reverse=True)
        
        return enhanced_movies
    
    def _update_user_preferences(self, user_id: str, mood: str, user_input: str):
        """更新用户偏好到向量数据库"""
        
        # 获取或创建用户会话
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'mood_history': [],
                'genre_preferences': [],
                'interaction_count': 0
            }
        
        session = self.user_sessions[user_id]
        session['mood_history'].append(mood)
        session['interaction_count'] += 1
        
        # 提取类型偏好
        genre_keywords = {
            '动作': ['动作', '打斗', '激动', '刺激'],
            '喜剧': ['搞笑', '幽默', '轻松', '开心'],
            '爱情': ['爱情', '浪漫', '情侣', '恋爱'],
            '科幻': ['科幻', '未来', '太空', '机器人'],
            '悬疑': ['悬疑', '推理', '犯罪', '侦探'],
            '治愈': ['治愈', '温暖', '感动', '温馨']
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                if genre not in session['genre_preferences']:
                    session['genre_preferences'].append(genre)
        
        # 每5次交互更新一次向量数据库
        if session['interaction_count'] % 5 == 0:
            preferences = {
                'favorite_genres': session['genre_preferences'],
                'mood_preferences': list(set(session['mood_history'][-10:])),  # 最近10次情绪
                'rating_range': [7.0, 10.0]  # 默认偏好高评分
            }
            
            self.milvus_db.add_user_preference(user_id, preferences)
    
    def _add_movies_to_vector_db_async(self, movies_data: List[Dict]):
        """异步添加电影到向量数据库"""
        try:
            # 简单的批量添加（实际项目中可以使用异步处理）
            processed_movies = []
            for movie in movies_data:
                if movie.get('title') and movie.get('overview'):
                    processed_movie = {
                        'id': f"tmdb_{movie.get('id', movie['title'])}",
                        'title': movie['title'],
                        'overview': movie['overview'],
                        'vote_average': movie.get('vote_average', 0),
                        'release_date': movie.get('release_date', ''),
                        'genres': movie.get('genre_ids', []),  # TMDB返回的是ID列表
                        'popularity': movie.get('popularity', 0)
                    }
                    processed_movies.append(processed_movie)
            
            if processed_movies:
                self.milvus_db.batch_add_movies(processed_movies)
                print(f"✅ 已添加 {len(processed_movies)} 部新电影到Milvus数据库")
        
        except Exception as e:
            print(f"添加电影到Milvus数据库失败：{e}")
    
    def _get_vector_recommendation_reason(self, movie: Dict, mood: str, similarity: float) -> str:
        """基于向量分析生成推荐理由"""
        title = movie.get('title', '')
        rating = movie.get('rating', 0)
        
        if similarity > 0.8:
            return f"《{title}》与您的{mood}情绪高度匹配，AI分析显示相似度达{similarity:.1%}"
        elif similarity > 0.6:
            return f"《{title}》很适合您当前的{mood}状态，评分{rating}分，值得一看"
        else:
            return f"《{title}》虽然匹配度中等，但评分{rating}分，可能会给您惊喜"
    
    def _extract_mood(self, user_input: str) -> str:
        """提取用户情绪"""
        mood_keywords = {
            "孤独": ["孤独", "一个人", "陌生城市", "独自"],
            "治愈": ["治愈", "温暖", "感动", "心情不好"],
            "压力": ["压力", "焦虑", "紧张", "累"],
            "开心": ["开心", "快乐", "爽", "搞笑"],
            "悲伤": ["难过", "悲伤", "失落", "沮丧"]
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                return mood
        
        return None
    
    def _get_mood_based_recommendations(self, mood: str, user_input: str) -> str:
        """基于情绪推荐电影"""
        
        # 获取对应情绪的电影
        movies = MOVIE_DATABASE.get(mood, MOVIE_DATABASE.get("治愈", []))
        
        result = f"🎭 **基于您的{mood}情绪推荐：**\n\n"
        
        for i, movie in enumerate(movies[:4], 1):
            title = movie.get('title', '')
            year = movie.get('year', '')
            director = movie.get('director', '')
            rating = movie.get('rating', 0)
            tags = movie.get('tags', [])
            
            result += f"{i}. **《{title}》** ({year})\n"
            result += f"   - 导演：{director}\n"
            result += f"   - 评分：{rating}/10\n"
            result += f"   - 标签：{', '.join(tags)}\n"
            result += f"   - 推荐理由：{self._get_recommendation_reason(movie, mood)}\n\n"
        
        # 添加个性化建议
        if "孤独" in user_input:
            result += "💡 **观影建议：**\n"
            result += "- 选择一个舒适的环境，准备一些小零食\n"
            result += "- 这些电影都能带来温暖和陪伴感\n"
            result += "- 观影后可以写写感受，有助于情感释放\n"
        
        return result
    
    def _get_recommendation_reason(self, movie: Dict, mood: str) -> str:
        """获取推荐理由"""
        title = movie.get('title', '')
        
        reasons = {
            "孤独": f"《{title}》能够带来温暖的陪伴感，让您在独处时也能感受到情感共鸣",
            "治愈": f"《{title}》具有强大的治愈力量，能够抚慰心灵，带来正能量",
            "压力": f"《{title}》有助于放松心情，暂时忘却生活中的压力和烦恼",
            "开心": f"《{title}》轻松幽默，能够带来欢乐和笑声",
            "悲伤": f"《{title}》能够引起情感共鸣，帮助您释放内心的情感"
        }
        
    
    def _extract_mood(self, user_input: str) -> str:
        """提取用户情绪"""
        mood_keywords = {
            "孤独": ["孤独", "一个人", "陌生城市", "独自"],
            "治愈": ["治愈", "温暖", "感动", "心情不好"],
            "压力": ["压力", "焦虑", "紧张", "累"],
            "开心": ["开心", "快乐", "爽", "搞笑"],
            "悲伤": ["难过", "悲伤", "失落", "沮丧"],
            "动作": ["动作", "刺激", "打斗", "激动"],
            "浪漫": ["浪漫", "爱情", "情侣", "恋爱"]
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                return mood
        
        return None
    
    def _get_mood_based_recommendations(self, mood: str, user_input: str) -> str:
        """基于情绪推荐电影（降级方案）"""
        
        # 获取对应情绪的电影
        movies = MOVIE_DATABASE.get(mood, MOVIE_DATABASE.get("治愈", []))
        
        result = f"🎭 **基于您的{mood}情绪推荐：**\n\n"
        
        for i, movie in enumerate(movies[:4], 1):
            title = movie.get('title', '')
            year = movie.get('year', '')
            director = movie.get('director', '')
            rating = movie.get('rating', 0)
            tags = movie.get('tags', [])
            
            result += f"{i}. **《{title}》** ({year})\n"
            result += f"   - 导演：{director}\n"
            result += f"   - 评分：{rating}/10\n"
            result += f"   - 标签：{', '.join(tags)}\n"
            result += f"   - 推荐理由：{self._get_recommendation_reason(movie, mood)}\n\n"
        
        # 添加个性化建议
        result += self._get_mood_specific_advice(mood)
        
        return result
    
    def _get_recommendation_reason(self, movie: Dict, mood: str) -> str:
        """获取推荐理由"""
        title = movie.get('title', '')
        
        reasons = {
            "孤独": f"《{title}》能够带来温暖的陪伴感，让您在独处时也能感受到情感共鸣",
            "治愈": f"《{title}》具有强大的治愈力量，能够抚慰心灵，带来正能量",
            "压力": f"《{title}》有助于放松心情，暂时忘却生活中的压力和烦恼",
            "开心": f"《{title}》轻松幽默，能够带来欢乐和笑声",
            "悲伤": f"《{title}》能够引起情感共鸣，帮助您释放内心的情感",
            "动作": f"《{title}》动作场面精彩，能够带来视觉冲击和肾上腺素飙升",
            "浪漫": f"《{title}》温馨浪漫，适合感受爱情的美好"
        }
        
        return reasons.get(mood, f"《{title}》是一部优秀的电影，值得观看")
    
    def _get_mood_specific_advice(self, mood: str) -> str:
        """获取针对特定情绪的观影建议"""
        advice_map = {
            "孤独": "💡 **观影建议：**\n- 选择一个舒适的环境，准备一些小零食\n- 这些电影都能带来温暖和陪伴感\n- 观影后可以写写感受，有助于情感释放\n",
            "治愈": "💡 **观影建议：**\n- 放松心情，让电影的温暖力量慢慢渗透\n- 可以准备一些纸巾，好电影总是会触动内心\n- 观影时专注当下，暂时放下烦恼\n",
            "压力": "💡 **观影建议：**\n- 关闭手机通知，完全沉浸在电影世界中\n- 选择舒适的观影姿势，让身心都得到放松\n- 观影时深呼吸，让紧张情绪随着剧情释放\n",
            "开心": "💡 **观影建议：**\n- 可以和朋友一起观看，分享快乐加倍\n- 准备一些零食和饮料，营造轻松氛围\n- 不要害怕大笑，释放内心的愉悦\n"
        }
        
        return advice_map.get(mood, "💡 享受观影时光，让电影带给您美好的体验！\n")
    
    def get_database_stats(self) -> Dict:
        """获取Milvus数据库统计信息"""
        try:
            return self.milvus_db.get_database_stats()
        except Exception as e:
            return {"error": str(e)}
    
    def search_similar_movies_by_title(self, movie_title: str, n_results: int = 5) -> List[Dict]:
        """根据电影标题搜索相似电影"""
        try:
            return self.milvus_db.search_similar_movies(
                query=f"电影：{movie_title}",
                n_results=n_results
            )
        except Exception as e:
            print(f"搜索相似电影失败：{e}")
            return []

# 创建全局实例
smart_agent = SmartMovieAgent()

def get_smart_response(user_input: str, user_id: str = "default_user") -> str:
    """智能Agent响应接口"""
    return smart_agent.chat(user_input, user_id)

# 向后兼容的接口
def get_simple_response(user_input: str) -> str:
    """向后兼容的响应接口"""
    return get_smart_response(user_input)
