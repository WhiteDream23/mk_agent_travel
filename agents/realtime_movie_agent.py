import requests
import json
from typing import Dict, List, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class RealTimeMovieDataAgent:
    """实时电影数据获取Agent"""
    
    def __init__(self):
        # 多个电影数据源API配置
        self.apis = {
            "tmdb": {
                "base_url": "https://api.themoviedb.org/3",
                "api_key": os.getenv("TMDB_API_KEY"),  # 需要申请TMDB API密钥
                "language": "zh-CN"
            },
            "douban": {
                "base_url": "https://movie.douban.com/j",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            },
            "maoyan": {
                "base_url": "https://piaofang.maoyan.com/api",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }
        }
        
    def get_now_playing_movies(self, city="北京", page=1) -> List[Dict]:
        """获取正在热映的电影"""
        movies = []
        
        # 尝试多个数据源
        try:
            # TMDB API - 正在上映
            tmdb_movies = self._get_tmdb_now_playing(page=page)
            movies.extend(tmdb_movies)
        except Exception as e:
            print(f"TMDB API错误: {e}")
        
        try:
            # 豆瓣正在热映
            douban_movies = self._get_douban_hot_movies()
            movies.extend(douban_movies)
        except Exception as e:
            print(f"豆瓣API错误: {e}")
        
        # 去重和整理
        return self._deduplicate_movies(movies)
    
    def get_upcoming_movies(self, weeks=4) -> List[Dict]:
        """获取即将上映的电影"""
        movies = []
        
        try:
            # TMDB即将上映
            tmdb_upcoming = self._get_tmdb_upcoming()
            movies.extend(tmdb_upcoming)
        except Exception as e:
            print(f"获取即将上映电影错误: {e}")
        
        return movies
    
    def search_movie_by_name(self, movie_name: str, year=None) -> Dict:
        """根据电影名搜索详细信息"""
        try:
            # 优先使用TMDB搜索
            return self._search_tmdb_movie(movie_name, year=year)
        except Exception as e:
            print(f"搜索电影错误: {e}")
            return {}
    
    def get_movie_showtimes(self, movie_name: str, city="北京") -> List[Dict]:
        """获取电影排片信息（这个需要实际的票务API）"""
        # 这里可以集成猫眼、淘票票等API
        # 由于这些API通常需要商业授权，这里提供模拟数据
        return self._get_mock_showtimes(movie_name, city)
    
    def get_box_office_data(self, date=None) -> Dict:
        """获取票房数据"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            return self._get_maoyan_box_office(date)
        except Exception as e:
            print(f"获取票房数据错误: {e}")
            return {}
    
    def _get_tmdb_now_playing(self, page=1) -> List[Dict]:
        """从TMDB获取正在上映的电影"""
        if not self.apis["tmdb"]["api_key"]:
            return []
        
        url = f"{self.apis['tmdb']['base_url']}/movie/now_playing"
        params = {
            "api_key": self.apis["tmdb"]["api_key"],
            "language": self.apis["tmdb"]["language"],
            "region": "CN",
            "page": page
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            movies = []
            
            for movie in data.get("results", [])[:10]:  # 取前10部
                movies.append({
                    "title": movie.get("title"),
                    "original_title": movie.get("original_title"),
                    "release_date": movie.get("release_date"),
                    "rating": movie.get("vote_average"),
                    "overview": movie.get("overview"),
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
                    "genres": self._get_movie_genres(movie.get("id")),
                    "source": "TMDB",
                    "status": "正在热映"
                })
            
            return movies
        
        return []
    
    def _get_douban_hot_movies(self) -> List[Dict]:
        """从豆瓣获取热门电影（注意：豆瓣API访问限制较多）"""
        try:
            # 豆瓣的公开API已经限制，这里提供备用方案
            # 实际使用中可能需要爬虫或其他方式
            url = "https://movie.douban.com/j/search_subjects"
            params = {
                "type": "movie",
                "tag": "热门",
                "sort": "recommend",
                "page_limit": 10,
                "page_start": 0
            }
            
            response = requests.get(url, params=params, 
                                  headers=self.apis["douban"]["headers"], 
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                movies = []
                
                for movie in data.get("subjects", []):
                    movies.append({
                        "title": movie.get("title"),
                        "rating": movie.get("rate"),
                        "poster_url": movie.get("cover"),
                        "douban_url": movie.get("url"),
                        "source": "豆瓣",
                        "status": "热门推荐"
                    })
                
                return movies
        
        except Exception as e:
            print(f"豆瓣API访问受限: {e}")
        
        return []
    
    def _search_tmdb_movie(self, movie_name: str, year=None) -> Dict:
        """在TMDB中搜索电影"""
        if not self.apis["tmdb"]["api_key"]:
            return {}
        
        url = f"{self.apis['tmdb']['base_url']}/search/movie"
        params = {
            "api_key": self.apis["tmdb"]["api_key"],
            "language": self.apis["tmdb"]["language"],
            "query": movie_name,
            "page": 1
        }
        
        if year:
            params["year"] = year
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if results:
                movie = results[0]  # 取第一个结果
                return {
                    "title": movie.get("title"),
                    "original_title": movie.get("original_title"),
                    "release_date": movie.get("release_date"),
                    "rating": movie.get("vote_average"),
                    "overview": movie.get("overview"),
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
                    "popularity": movie.get("popularity"),
                    "vote_count": movie.get("vote_count"),
                    "source": "TMDB"
                }
        
        return {}
    
    def _get_tmdb_upcoming(self) -> List[Dict]:
        """获取即将上映的电影"""
        if not self.apis["tmdb"]["api_key"]:
            return []
        
        url = f"{self.apis['tmdb']['base_url']}/movie/upcoming"
        params = {
            "api_key": self.apis["tmdb"]["api_key"],
            "language": self.apis["tmdb"]["language"],
            "region": "CN",
            "page": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            movies = []
            
            for movie in data.get("results", [])[:10]:
                movies.append({
                    "title": movie.get("title"),
                    "original_title": movie.get("original_title"),
                    "release_date": movie.get("release_date"),
                    "rating": movie.get("vote_average"),
                    "overview": movie.get("overview"),
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
                    "source": "TMDB",
                    "status": "即将上映"
                })
            
            return movies
        
        return []
    
    def _get_movie_genres(self, movie_id: int) -> List[str]:
        """获取电影类型"""
        if not self.apis["tmdb"]["api_key"] or not movie_id:
            return []
        
        try:
            url = f"{self.apis['tmdb']['base_url']}/movie/{movie_id}"
            params = {
                "api_key": self.apis["tmdb"]["api_key"],
                "language": self.apis["tmdb"]["language"]
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [genre["name"] for genre in data.get("genres", [])]
        
        except Exception:
            pass
        
        return []
    
    def _get_mock_showtimes(self, movie_name: str, city: str) -> List[Dict]:
        """模拟排片信息（实际应用中需要接入真实票务API）"""
        # 这里提供模拟数据，实际使用时需要接入猫眼、淘票票等API
        mock_cinemas = [
            "万达影城", "CGV影城", "博纳国际影城", "金逸影城", "大地影院"
        ]
        
        mock_times = [
            "10:30", "13:20", "15:50", "18:40", "21:10"
        ]
        
        showtimes = []
        for cinema in mock_cinemas[:3]:
            for time in mock_times[:3]:
                showtimes.append({
                    "cinema": cinema,
                    "time": time,
                    "hall": f"{len(showtimes) + 1}号厅",
                    "price": f"¥{35 + len(showtimes) * 5}",
                    "seats_available": f"{80 - len(showtimes) * 10}个座位"
                })
        
        return showtimes
    
    def _get_maoyan_box_office(self, date: str) -> Dict:
        """获取票房数据（模拟，实际需要商业API）"""
        # 实际使用中需要接入猫眼专业版或其他票房数据API
        return {
            "date": date,
            "total_box_office": "1.2亿",
            "top_movies": [
                {"rank": 1, "title": "热门电影1", "box_office": "3000万", "attendance": "85万人"},
                {"rank": 2, "title": "热门电影2", "box_office": "2500万", "attendance": "70万人"},
                {"rank": 3, "title": "热门电影3", "box_office": "2000万", "attendance": "60万人"}
            ]
        }
    
    def _deduplicate_movies(self, movies: List[Dict]) -> List[Dict]:
        """去重电影列表"""
        seen_titles = set()
        unique_movies = []
        
        for movie in movies:
            title = movie.get("title", "").lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_movies.append(movie)
        
        return unique_movies

# 创建全局实例
real_time_movie_agent = RealTimeMovieDataAgent()
