"""
简化版的电影推荐Agent
"""

import os
from typing import Dict, List
import json
from agents.realtime_movie_agent import RealTimeMovieDataAgent
from agents.movie_database_agent import MOVIE_DATABASE

class SimpleMovieAgent:
    def __init__(self):
        self.realtime_agent = RealTimeMovieDataAgent()
        
    def chat(self, user_input: str) -> str:
        """处理用户输入并返回推荐"""
        
        # 检查是否需要实时数据
        if any(keyword in user_input for keyword in ["最新", "热映", "正在上映", "最近", "院线"]):
            return self._get_now_playing_recommendations(user_input)
        
        # 检查情绪关键词
        mood = self._extract_mood(user_input)
        if mood:
            return self._get_mood_based_recommendations(mood, user_input)
        
        # 默认推荐
        return self._get_general_recommendations()
    
    def _get_now_playing_recommendations(self, user_input: str) -> str:
        """获取正在热映的电影推荐"""
        try:
            # 直接调用实时API
            movies = self.realtime_agent.get_now_playing_movies()
            
            if movies:
                result = "🎬 **当前正在热映的电影推荐：**\n\n"
                
                # 解析JSON数据
                if isinstance(movies, str):
                    movies_data = json.loads(movies)
                else:
                    movies_data = movies
                
                for i, movie in enumerate(movies_data[:5], 1):
                    title = movie.get('title', '未知电影')
                    rating = movie.get('vote_average', 0)
                    overview = movie.get('overview', '暂无简介')
                    release_date = movie.get('release_date', '未知')
                    
                    result += f"{i}. **《{title}》**\n"
                    result += f"   - 评分：{rating}/10\n"
                    result += f"   - 上映日期：{release_date}\n"
                    result += f"   - 简介：{overview[:100]}...\n\n"
                
                # 基于用户情绪添加个性化建议
                if "孤独" in user_input or "一个人" in user_input:
                    result += "💡 **针对您的情况特别推荐：**\n"
                    result += "考虑到您一个人在陌生城市，建议选择温暖治愈系的电影，\n"
                    result += "可以在观影中获得情感慰藉和心灵放松。\n\n"
                
                result += "🎫 您可以通过各大购票平台查看具体排片时间和购票信息。"
                return result
            else:
                return "抱歉，暂时无法获取最新的电影信息，请稍后再试。"
                
        except Exception as e:
            print(f"获取实时电影数据失败：{e}")
            return "抱歉，获取实时电影数据时出现问题，让我为您推荐一些经典的治愈电影。\n\n" + self._get_fallback_recommendations()
    
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
        
        return reasons.get(mood, f"《{title}》是一部优秀的电影，值得观看")
    
    def _get_general_recommendations(self) -> str:
        """通用推荐"""
        result = "🎬 **为您推荐一些优质电影：**\n\n"
        
        # 从不同类型中选择
        featured_movies = []
        for mood_type, movies in MOVIE_DATABASE.items():
            if movies:
                featured_movies.append(movies[0])  # 每个类型选一部
        
        for i, movie in enumerate(featured_movies[:5], 1):
            title = movie.get('title', '')
            year = movie.get('year', '')
            rating = movie.get('rating', 0)
            tags = movie.get('tags', [])
            
            result += f"{i}. **《{title}》** ({year})\n"
            result += f"   - 评分：{rating}/10\n"
            result += f"   - 类型：{', '.join(tags)}\n\n"
        
        result += "💡 如果您想要更个性化的推荐，请告诉我您的心情或喜好！"
        
        return result
    
    def _get_fallback_recommendations(self) -> str:
        """备用推荐（当API失败时）"""
        movies = MOVIE_DATABASE.get("治愈", [])[:3]
        
        result = "🎬 **经典治愈电影推荐：**\n\n"
        
        for i, movie in enumerate(movies, 1):
            title = movie.get('title', '')
            year = movie.get('year', '')
            rating = movie.get('rating', 0)
            
            result += f"{i}. **《{title}》** ({year}) - 评分：{rating}/10\n"
        
        return result

# 创建全局实例
simple_agent = SimpleMovieAgent()

def get_simple_response(user_input: str) -> str:
    """简单Agent响应接口"""
    return simple_agent.chat(user_input)
