"""
Milvus向量数据库管理器
高性能向量检索和电影推荐系统
"""

import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pymilvus import (
    connections, utility, FieldSchema, CollectionSchema,
    Collection, DataType, Index
)
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusMovieDB:
    """基于Milvus的电影向量数据库管理器"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: str = "19530",
                 collection_name: str = "movie_collection",
                 user_collection_name: str = "user_collection"):
        """
        初始化Milvus向量数据库
        
        Args:
            host: Milvus服务器地址
            port: Milvus端口
            collection_name: 电影集合名称
            user_collection_name: 用户集合名称
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.user_collection_name = user_collection_name
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.vector_dim = 384  # 模型向量维度
        
        # 初始化嵌入模型
        logger.info("🤖 正在加载向量模型...")
        self.embedding_model = SentenceTransformer(self.model_name)
        
        # 连接Milvus
        self._connect_milvus()
        
        # 创建集合
        self.movie_collection = self._create_movie_collection()
        self.user_collection = self._create_user_collection()
        
        logger.info("✅ Milvus向量数据库初始化完成")
    
    def _connect_milvus(self):
        """连接到Milvus服务器"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"✅ 已连接到Milvus服务器 {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ 连接Milvus失败：{e}")
            logger.info("💡 请确保Milvus服务器正在运行")
            logger.info("🚀 启动Milvus: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest standalone")
            raise
    
    def _create_movie_collection(self) -> Collection:
        """创建电影集合"""
        # 检查集合是否存在
        if utility.has_collection(self.collection_name):
            logger.info(f"📚 集合 {self.collection_name} 已存在")
            return Collection(self.collection_name)
        
        # 定义字段schema
        fields = [
            FieldSchema(name="movie_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="director", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="year", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="rating", dtype=DataType.FLOAT),
            FieldSchema(name="popularity", dtype=DataType.FLOAT),
            FieldSchema(name="genres", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="overview", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="mood_tags", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="added_date", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim)
        ]
        
        # 创建集合schema
        schema = CollectionSchema(
            fields=fields,
            description="Movie recommendation collection with embeddings"
        )
        
        # 创建集合
        collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",  # 余弦相似度
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info(f"✅ 创建电影集合 {self.collection_name}")
        return collection
    
    def _create_user_collection(self) -> Collection:
        """创建用户偏好集合"""
        # 检查集合是否存在
        if utility.has_collection(self.user_collection_name):
            logger.info(f"👥 集合 {self.user_collection_name} 已存在")
            return Collection(self.user_collection_name)
        
        # 定义字段schema
        fields = [
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="preferences", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="interaction_count", dtype=DataType.INT64),
            FieldSchema(name="last_updated", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim)
        ]
        
        # 创建集合schema
        schema = CollectionSchema(
            fields=fields,
            description="User preferences collection with embeddings"
        )
        
        # 创建集合
        collection = Collection(
            name=self.user_collection_name,
            schema=schema
        )
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 32}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info(f"✅ 创建用户集合 {self.user_collection_name}")
        return collection
    
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
        
        # 准备数据
        entities = [
            [movie_id],  # movie_id
            [movie_data.get('title', '')],  # title
            [movie_data.get('director', '')],  # director
            [str(movie_data.get('year', movie_data.get('release_date', '')))],  # year
            [float(movie_data.get('rating', movie_data.get('vote_average', 0)))],  # rating
            [float(movie_data.get('popularity', 0))],  # popularity
            [json.dumps(movie_data.get('genres', movie_data.get('tags', [])), ensure_ascii=False)],  # genres
            [movie_data.get('overview', '')[:2000]],  # overview (限制长度)
            [movie_data.get('mood_tag', '')],  # mood_tags
            [datetime.now().isoformat()],  # added_date
            [embedding]  # embedding
        ]
        
        # 插入数据
        self.movie_collection.insert(entities)
        self.movie_collection.flush()
        
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
        
        # 情绪标签
        mood_tag = movie_data.get('mood_tag', '')
        if mood_tag:
            parts.append(f"情绪：{mood_tag}")
        
        return ". ".join(parts)
    
    def search_similar_movies(self, 
                            query: str = None, 
                            movie_id: str = None,
                            n_results: int = 5,
                            filters: str = None) -> List[Dict]:
        """
        搜索相似电影
        
        Args:
            query: 文本查询
            movie_id: 基于某部电影查找相似
            n_results: 返回结果数量
            filters: 过滤条件表达式
            
        Returns:
            相似电影列表
        """
        self.movie_collection.load()
        
        if query:
            # 基于文本查询
            query_embedding = self.embedding_model.encode(query).tolist()
            search_vectors = [query_embedding]
        elif movie_id:
            # 基于电影ID查找相似
            # 首先获取该电影的向量
            expr = f'movie_id == "{movie_id}"'
            results = self.movie_collection.query(
                expr=expr,
                output_fields=["embedding"]
            )
            
            if not results:
                return []
            
            search_vectors = [results[0]["embedding"]]
            n_results += 1  # +1 因为会包含自己
        else:
            return []
        
        # 执行向量搜索
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = self.movie_collection.search(
            data=search_vectors,
            anns_field="embedding",
            param=search_params,
            limit=n_results,
            output_fields=["movie_id", "title", "director", "year", "rating", "popularity", "genres", "overview", "mood_tags"],
            expr=filters
        )
        
        # 格式化结果
        similar_movies = []
        if results and len(results) > 0:
            for hit in results[0]:
                # 如果是基于movie_id搜索，跳过自己
                if movie_id and hit.entity.get("movie_id") == movie_id:
                    continue
                
                genres_str = hit.entity.get("genres", "[]")
                try:
                    genres = json.loads(genres_str) if genres_str else []
                except:
                    genres = []
                
                movie = {
                    'id': hit.entity.get("movie_id"),
                    'similarity': 1 - hit.distance,  # 转换为相似度
                    'title': hit.entity.get("title", ''),
                    'year': hit.entity.get("year", ''),
                    'genre': genres,
                    'rating': hit.entity.get("rating", 0),
                    'director': hit.entity.get("director", ''),
                    'overview': hit.entity.get("overview", ''),
                    'popularity': hit.entity.get("popularity", 0),
                    'mood_tags': hit.entity.get("mood_tags", '')
                }
                similar_movies.append(movie)
        
        return similar_movies
    
    def add_user_preference(self, user_id: str, preferences: Dict):
        """添加用户偏好到向量数据库"""
        # 构建偏好文本
        pref_text = self._build_preference_text(preferences)
        
        # 生成向量
        embedding = self.embedding_model.encode(pref_text).tolist()
        
        # 检查用户是否已存在
        self.user_collection.load()
        expr = f'user_id == "{user_id}"'
        existing = self.user_collection.query(
            expr=expr,
            output_fields=["user_id", "interaction_count"]
        )
        
        interaction_count = 1
        if existing:
            interaction_count = existing[0].get("interaction_count", 0) + 1
            # 删除旧记录
            self.user_collection.delete(expr)
        
        # 准备数据
        entities = [
            [user_id],  # user_id
            [json.dumps(preferences, ensure_ascii=False)],  # preferences
            [interaction_count],  # interaction_count
            [datetime.now().isoformat()],  # last_updated
            [embedding]  # embedding
        ]
        
        # 插入数据
        self.user_collection.insert(entities)
        self.user_collection.flush()
    
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
        
        self.user_collection.load()
        
        # 获取用户偏好
        expr = f'user_id == "{user_id}"'
        user_data = self.user_collection.query(
            expr=expr,
            output_fields=["preferences"]
        )
        
        if not user_data:
            # 用户不存在，返回热门电影
            return self.get_popular_movies(n_results)
        
        # 构建查询
        query_parts = []
        user_prefs = json.loads(user_data[0]["preferences"])
        
        # 添加情绪信息
        if mood:
            query_parts.append(f"情绪：{mood}")
        
        # 添加用户偏好
        if user_prefs.get('favorite_genres'):
            query_parts.append(f"类型：{', '.join(user_prefs['favorite_genres'])}")
        
        query = ". ".join(query_parts) if query_parts else "推荐电影"
        
        # 设置过滤条件
        filters = None
        if user_prefs.get('rating_range'):
            filters = f"rating >= {user_prefs['rating_range'][0]}"
        
        return self.search_similar_movies(query=query, n_results=n_results, filters=filters)
    
    def get_popular_movies(self, n_results: int = 10) -> List[Dict]:
        """获取热门电影"""
        self.movie_collection.load()
        
        # 按评分和受欢迎程度排序
        results = self.movie_collection.query(
            expr="rating >= 7.0",
            output_fields=["movie_id", "title", "year", "rating", "popularity", "genres"],
            limit=n_results
        )
        
        movies = []
        for result in results:
            genres_str = result.get("genres", "[]")
            try:
                genres = json.loads(genres_str) if genres_str else []
            except:
                genres = []
            
            movie = {
                'id': result.get("movie_id"),
                'title': result.get("title", ''),
                'year': result.get("year", ''),
                'genre': genres,
                'rating': result.get("rating", 0),
                'popularity': result.get("popularity", 0)
            }
            movies.append(movie)
        
        # 按评分和受欢迎程度排序
        movies.sort(key=lambda x: (x['rating'], x['popularity']), reverse=True)
        return movies
    
    def update_movie_ratings(self, movie_id: str, new_rating: float):
        """更新电影评分"""
        try:
            # Milvus不支持直接更新，需要删除后重新插入
            # 这里只是示例，实际应用中可能需要更复杂的更新策略
            expr = f'movie_id == "{movie_id}"'
            results = self.movie_collection.query(
                expr=expr,
                output_fields=["*"]
            )
            
            if results:
                # 删除旧记录
                self.movie_collection.delete(expr)
                
                # 更新评分并重新插入
                movie_data = results[0]
                movie_data['rating'] = new_rating
                self.add_movie(movie_data)
                
        except Exception as e:
            logger.error(f"更新评分失败：{e}")
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        try:
            movies_count = self.movie_collection.num_entities
            users_count = self.user_collection.num_entities
            
            return {
                "movies_count": movies_count,
                "users_count": users_count,
                "model_name": self.model_name,
                "host": self.host,
                "port": self.port,
                "vector_dim": self.vector_dim
            }
        except Exception as e:
            return {
                "error": str(e),
                "movies_count": 0,
                "users_count": 0
            }
    
    def batch_add_movies(self, movies_list: List[Dict]) -> List[str]:
        """批量添加电影"""
        logger.info(f"🔄 正在批量处理 {len(movies_list)} 部电影...")
        
        # 准备批量数据
        movie_ids = []
        titles = []
        directors = []
        years = []
        ratings = []
        popularities = []
        genres_list = []
        overviews = []
        mood_tags = []
        added_dates = []
        embeddings = []
        
        for movie_data in movies_list:
            movie_id = str(movie_data.get('id', movie_data.get('title', '')))
            movie_ids.append(movie_id)
            
            # 构建文本和向量
            text_for_embedding = self._build_movie_text(movie_data)
            embedding = self.embedding_model.encode(text_for_embedding).tolist()
            
            titles.append(movie_data.get('title', ''))
            directors.append(movie_data.get('director', ''))
            years.append(str(movie_data.get('year', movie_data.get('release_date', ''))))
            ratings.append(float(movie_data.get('rating', movie_data.get('vote_average', 0))))
            popularities.append(float(movie_data.get('popularity', 0)))
            genres_list.append(json.dumps(movie_data.get('genres', movie_data.get('tags', [])), ensure_ascii=False))
            overviews.append(movie_data.get('overview', '')[:2000])
            mood_tags.append(movie_data.get('mood_tag', ''))
            added_dates.append(datetime.now().isoformat())
            embeddings.append(embedding)
        
        # 批量插入
        entities = [
            movie_ids,
            titles,
            directors,
            years,
            ratings,
            popularities,
            genres_list,
            overviews,
            mood_tags,
            added_dates,
            embeddings
        ]
        
        self.movie_collection.insert(entities)
        self.movie_collection.flush()
        
        logger.info(f"✅ 成功添加 {len(movie_ids)} 部电影到Milvus数据库")
        return movie_ids
    
    def close_connection(self):
        """关闭数据库连接"""
        try:
            connections.disconnect("default")
            logger.info("✅ 已断开Milvus连接")
        except Exception as e:
            logger.error(f"断开连接失败：{e}")

# 全局向量数据库实例
milvus_db = None

def get_milvus_db() -> MilvusMovieDB:
    """获取Milvus数据库实例（单例模式）"""
    global milvus_db
    if milvus_db is None:
        milvus_db = MilvusMovieDB()
    return milvus_db

def init_milvus_db_with_sample_data():
    """使用示例数据初始化Milvus数据库"""
    from agents.movie_database_agent import MOVIE_DATABASE
    
    db = get_milvus_db()
    
    # 检查是否已有数据
    stats = db.get_database_stats()
    if stats.get('movies_count', 0) > 0:
        logger.info(f"📊 Milvus数据库已有 {stats['movies_count']} 部电影")
        return db
    
    # 准备示例数据
    all_movies = []
    movie_id = 1
    
    for mood, movies in MOVIE_DATABASE.items():
        for movie in movies:
            movie_with_id = movie.copy()
            movie_with_id['id'] = f"local_{movie_id}"
            movie_with_id['mood_tag'] = mood
            if 'tags' in movie_with_id:
                movie_with_id['genres'] = movie_with_id['tags']
            all_movies.append(movie_with_id)
            movie_id += 1
    
    # 批量添加到Milvus数据库
    db.batch_add_movies(all_movies)
    
    logger.info(f"🎬 Milvus数据库初始化完成，共 {len(all_movies)} 部电影")
    return db
