"""
向量数据库管理器
用于电影数据的向量化存储、相似性检索和个性化推荐
"""

import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime

class MovieVectorDB:
    """电影向量数据库管理器"""
    
    def __init__(self, db_path: str = "./movie_vectors"):
        """
        初始化向量数据库
        
        Args:
            db_path: 数据库存储路径
        """
        self.db_path = db_path
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # 多语言模型
        
        # 初始化嵌入模型
        print("🤖 正在加载向量模型...")
        self.embedding_model = SentenceTransformer(self.model_name)
        
        # 初始化ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 创建集合
        self.movies_collection = self._get_or_create_collection("movies")
        self.users_collection = self._get_or_create_collection("user_preferences")
        
        print("✅ 向量数据库初始化完成")
    
    def _get_or_create_collection(self, collection_name: str):
        """获取或创建集合"""
        try:
            return self.client.get_collection(collection_name)
        except:
            return self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
    
    def add_movie(self, movie_data: Dict) -> str:
        """
        添加电影到向量数据库
        
        Args:
            movie_data: 电影数据字典
            
        Returns:
            电影ID
        """
        movie_id = str(movie_data.get('id', movie_data.get('title', '')))
        
        # 构建用于向量化的文本
        text_for_embedding = self._build_movie_text(movie_data)
        
        # 生成向量
        embedding = self.embedding_model.encode(text_for_embedding).tolist()
        
        # 准备元数据
        metadata = {
            "title": movie_data.get('title', ''),
            "year": str(movie_data.get('year', movie_data.get('release_date', ''))),
            "genre": json.dumps(movie_data.get('genres', movie_data.get('tags', []))),
            "rating": float(movie_data.get('rating', movie_data.get('vote_average', 0))),
            "director": movie_data.get('director', ''),
            "overview": movie_data.get('overview', '')[:500],  # 限制长度
            "popularity": float(movie_data.get('popularity', 0)),
            "added_date": datetime.now().isoformat()
        }
        
        # 添加到数据库
        self.movies_collection.add(
            embeddings=[embedding],
            documents=[text_for_embedding],
            metadatas=[metadata],
            ids=[movie_id]
        )
        
        return movie_id
    
    def _build_movie_text(self, movie_data: Dict) -> str:
        """构建电影的文本描述用于向量化"""
        parts = []
        
        # 标题
        if movie_data.get('title'):
            parts.append(f"电影：{movie_data['title']}")
        
        # 类型/标签
        genres = movie_data.get('genres', movie_data.get('tags', []))
        if genres:
            if isinstance(genres, list):
                parts.append(f"类型：{', '.join(genres)}")
            else:
                parts.append(f"类型：{genres}")
        
        # 导演
        if movie_data.get('director'):
            parts.append(f"导演：{movie_data['director']}")
        
        # 简介
        overview = movie_data.get('overview', '')
        if overview:
            parts.append(f"简介：{overview}")
        
        # 年份
        year = movie_data.get('year', movie_data.get('release_date', ''))
        if year:
            parts.append(f"年份：{year}")
        
        return ". ".join(parts)
    
    def search_similar_movies(self, 
                            query: str = None, 
                            movie_id: str = None,
                            n_results: int = 5,
                            filters: Dict = None) -> List[Dict]:
        """
        搜索相似电影
        
        Args:
            query: 文本查询
            movie_id: 基于某部电影查找相似
            n_results: 返回结果数量
            filters: 过滤条件
            
        Returns:
            相似电影列表
        """
        if query:
            # 基于文本查询
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.movies_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters
            )
        elif movie_id:
            # 基于电影ID查找相似
            movie_data = self.movies_collection.get(ids=[movie_id])
            if not movie_data['embeddings']:
                return []
            
            results = self.movies_collection.query(
                query_embeddings=movie_data['embeddings'],
                n_results=n_results + 1,  # +1 因为会包含自己
                where=filters
            )
            
            # 移除自己
            if results['ids'][0] and movie_id in results['ids'][0]:
                idx = results['ids'][0].index(movie_id)
                for key in results:
                    if isinstance(results[key], list) and len(results[key]) > 0:
                        results[key][0].pop(idx)
        else:
            return []
        
        # 格式化结果
        similar_movies = []
        if results['ids'][0]:  # 确保有结果
            for i in range(len(results['ids'][0])):
                movie = {
                    'id': results['ids'][0][i],
                    'similarity': 1 - results['distances'][0][i],  # 转换为相似度
                    'title': results['metadatas'][0][i].get('title', ''),
                    'year': results['metadatas'][0][i].get('year', ''),
                    'genre': json.loads(results['metadatas'][0][i].get('genre', '[]')),
                    'rating': results['metadatas'][0][i].get('rating', 0),
                    'director': results['metadatas'][0][i].get('director', ''),
                    'overview': results['metadatas'][0][i].get('overview', ''),
                    'popularity': results['metadatas'][0][i].get('popularity', 0)
                }
                similar_movies.append(movie)
        
        return similar_movies
    
    def add_user_preference(self, user_id: str, preferences: Dict):
        """添加用户偏好到向量数据库"""
        # 构建偏好文本
        pref_text = self._build_preference_text(preferences)
        
        # 生成向量
        embedding = self.embedding_model.encode(pref_text).tolist()
        
        # 元数据
        metadata = {
            "user_id": user_id,
            "preferences": json.dumps(preferences),
            "updated_date": datetime.now().isoformat()
        }
        
        # 检查用户是否已存在
        existing = self.users_collection.get(ids=[user_id])
        if existing['ids']:
            # 更新
            self.users_collection.update(
                ids=[user_id],
                embeddings=[embedding],
                documents=[pref_text],
                metadatas=[metadata]
            )
        else:
            # 添加
            self.users_collection.add(
                embeddings=[embedding],
                documents=[pref_text],
                metadatas=[metadata],
                ids=[user_id]
            )
    
    def _build_preference_text(self, preferences: Dict) -> str:
        """构建用户偏好文本"""
        parts = []
        
        if preferences.get('favorite_genres'):
            parts.append(f"喜欢的类型：{', '.join(preferences['favorite_genres'])}")
        
        if preferences.get('mood_preferences'):
            parts.append(f"情绪偏好：{', '.join(preferences['mood_preferences'])}")
        
        if preferences.get('favorite_directors'):
            parts.append(f"喜欢的导演：{', '.join(preferences['favorite_directors'])}")
        
        if preferences.get('rating_range'):
            parts.append(f"评分范围：{preferences['rating_range'][0]}-{preferences['rating_range'][1]}")
        
        return ". ".join(parts)
    
    def get_personalized_recommendations(self, 
                                       user_id: str, 
                                       mood: str = None,
                                       n_results: int = 10) -> List[Dict]:
        """基于用户偏好获取个性化推荐"""
        
        # 获取用户偏好
        user_data = self.users_collection.get(ids=[user_id])
        if not user_data['embeddings']:
            # 用户不存在，返回热门电影
            return self.get_popular_movies(n_results)
        
        # 构建查询
        query_parts = []
        user_prefs = json.loads(user_data['metadatas'][0]['preferences'])
        
        # 添加情绪信息
        if mood:
            query_parts.append(f"情绪：{mood}")
        
        # 添加用户偏好
        if user_prefs.get('favorite_genres'):
            query_parts.append(f"类型：{', '.join(user_prefs['favorite_genres'])}")
        
        query = ". ".join(query_parts) if query_parts else "推荐电影"
        
        # 设置过滤条件
        filters = {}
        if user_prefs.get('rating_range'):
            filters["rating"] = {"$gte": user_prefs['rating_range'][0]}
        
        return self.search_similar_movies(query=query, n_results=n_results, filters=filters)
    
    def get_popular_movies(self, n_results: int = 10) -> List[Dict]:
        """获取热门电影"""
        results = self.movies_collection.query(
            query_embeddings=[np.zeros(384).tolist()],  # 模型维度
            n_results=n_results,
            where={"rating": {"$gte": 7.0}}  # 评分>=7.0
        )
        
        movies = []
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                movie = {
                    'id': results['ids'][0][i],
                    'title': results['metadatas'][0][i].get('title', ''),
                    'year': results['metadatas'][0][i].get('year', ''),
                    'genre': json.loads(results['metadatas'][0][i].get('genre', '[]')),
                    'rating': results['metadatas'][0][i].get('rating', 0),
                    'popularity': results['metadatas'][0][i].get('popularity', 0)
                }
                movies.append(movie)
        
        # 按评分和受欢迎程度排序
        movies.sort(key=lambda x: (x['rating'], x['popularity']), reverse=True)
        return movies
    
    def update_movie_ratings(self, movie_id: str, new_rating: float):
        """更新电影评分"""
        try:
            self.movies_collection.update(
                ids=[movie_id],
                metadatas=[{"rating": new_rating}]
            )
        except Exception as e:
            print(f"更新评分失败：{e}")
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        movies_count = self.movies_collection.count()
        users_count = self.users_collection.count()
        
        return {
            "movies_count": movies_count,
            "users_count": users_count,
            "model_name": self.model_name,
            "db_path": self.db_path
        }
    
    def batch_add_movies(self, movies_list: List[Dict]) -> List[str]:
        """批量添加电影"""
        movie_ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        print(f"🔄 正在处理 {len(movies_list)} 部电影...")
        
        for movie_data in movies_list:
            movie_id = str(movie_data.get('id', movie_data.get('title', '')))
            movie_ids.append(movie_id)
            
            # 构建文本和向量
            text_for_embedding = self._build_movie_text(movie_data)
            documents.append(text_for_embedding)
            
            # 生成向量
            embedding = self.embedding_model.encode(text_for_embedding).tolist()
            embeddings.append(embedding)
            
            # 准备元数据
            metadata = {
                "title": movie_data.get('title', ''),
                "year": str(movie_data.get('year', movie_data.get('release_date', ''))),
                "genre": json.dumps(movie_data.get('genres', movie_data.get('tags', []))),
                "rating": float(movie_data.get('rating', movie_data.get('vote_average', 0))),
                "director": movie_data.get('director', ''),
                "overview": movie_data.get('overview', '')[:500],
                "popularity": float(movie_data.get('popularity', 0)),
                "added_date": datetime.now().isoformat()
            }
            metadatas.append(metadata)
        
        # 批量添加
        self.movies_collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=movie_ids
        )
        
        print(f"✅ 成功添加 {len(movie_ids)} 部电影到向量数据库")
        return movie_ids

# 全局向量数据库实例
vector_db = None

def get_vector_db() -> MovieVectorDB:
    """获取向量数据库实例（单例模式）"""
    global vector_db
    if vector_db is None:
        vector_db = MovieVectorDB()
    return vector_db

def init_vector_db_with_sample_data():
    """使用示例数据初始化向量数据库"""
    from agents.movie_database_agent import MOVIE_DATABASE
    
    db = get_vector_db()
    
    # 检查是否已有数据
    stats = db.get_database_stats()
    if stats['movies_count'] > 0:
        print(f"📊 向量数据库已有 {stats['movies_count']} 部电影")
        return db
    
    # 准备示例数据
    all_movies = []
    movie_id = 1
    
    for mood, movies in MOVIE_DATABASE.items():
        for movie in movies:
            movie_with_id = movie.copy()
            movie_with_id['id'] = movie_id
            movie_with_id['mood_tag'] = mood
            if 'tags' in movie_with_id:
                movie_with_id['genres'] = movie_with_id['tags']
            all_movies.append(movie_with_id)
            movie_id += 1
    
    # 批量添加到向量数据库
    db.batch_add_movies(all_movies)
    
    print(f"🎬 向量数据库初始化完成，共 {len(all_movies)} 部电影")
    return db
