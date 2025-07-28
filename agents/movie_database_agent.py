from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import json
import random

# 加载 .env 文件
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("请在 .env 文件中设置 OPENAI_API_KEY")

llm = ChatOpenAI(
    temperature=0.4,
    model="Qwen/Qwen3-8B",
    api_key=api_key,
    base_url="https://api.siliconflow.cn/v1"
)

# 扩展的电影数据库
MOVIE_DATABASE = {
    "搞笑": [
        {"title": "夏洛特烦恼", "year": 2015, "director": "闫非", "rating": 8.2, "tags": ["穿越", "校园", "爱情"]},
        {"title": "西虹市首富", "year": 2018, "director": "闫非", "rating": 7.8, "tags": ["金钱", "梦想", "喜剧"]},
        {"title": "羞羞的铁拳", "year": 2017, "director": "宋阳", "rating": 7.5, "tags": ["性别互换", "拳击", "爱情"]},
        {"title": "疯狂的石头", "year": 2006, "director": "宁浩", "rating": 8.5, "tags": ["黑色幽默", "多线叙事"]},
        {"title": "泰囧", "year": 2012, "director": "徐峥", "rating": 7.3, "tags": ["公路", "冒险", "友情"]}
    ],
    "治愈": [
        {"title": "小森林", "year": 2018, "director": "李廷香", "rating": 8.0, "tags": ["田园", "美食", "成长"]},
        {"title": "菊次郎的夏天", "year": 1999, "director": "北野武", "rating": 8.7, "tags": ["童年", "友情", "温暖"]},
        {"title": "海蒂和爷爷", "year": 2015, "director": "阿兰·葛斯彭纳", "rating": 9.2, "tags": ["亲情", "自然", "童真"]},
        {"title": "放牛班的春天", "year": 2004, "director": "克里斯托夫·巴拉蒂", "rating": 9.3, "tags": ["音乐", "教育", "希望"]},
        {"title": "龙猫", "year": 1988, "director": "宫崎骏", "rating": 9.2, "tags": ["动画", "童话", "想象力"]}
    ],
    "热血": [
        {"title": "灌篮高手", "year": 1995, "director": "西泽信孝", "rating": 9.6, "tags": ["篮球", "青春", "梦想"]},
        {"title": "摔跤吧！爸爸", "year": 2016, "director": "尼特什·提瓦瑞", "rating": 9.0, "tags": ["体育", "父女", "励志"]},
        {"title": "烈火英雄", "year": 2019, "director": "陈国辉", "rating": 7.8, "tags": ["消防", "英雄", "牺牲"]},
        {"title": "中国女排", "year": 2020, "director": "陈可辛", "rating": 7.3, "tags": ["排球", "团队", "拼搏"]},
        {"title": "少年的你", "year": 2019, "director": "曾国祥", "rating": 8.3, "tags": ["校园霸凌", "成长", "保护"]}
    ],
    "浪漫": [
        {"title": "你的名字", "year": 2016, "director": "新海诚", "rating": 8.4, "tags": ["穿越", "命运", "初恋"]},
        {"title": "怦然心动", "year": 2010, "director": "罗伯·莱纳", "rating": 9.0, "tags": ["青春", "初恋", "成长"]},
        {"title": "泰坦尼克号", "year": 1997, "director": "詹姆斯·卡梅隆", "rating": 9.4, "tags": ["史诗", "悲剧", "经典"]},
        {"title": "我和我的家乡", "year": 2020, "director": "宁浩", "rating": 7.8, "tags": ["亲情", "思乡", "温情"]},
        {"title": "比悲伤更悲伤的故事", "year": 2018, "director": "林孝谦", "rating": 7.5, "tags": ["纯爱", "疾病", "牺牲"]}
    ],
    "悲伤": [
        {"title": "忠犬八公的故事", "year": 2009, "director": "拉斯·霍尔斯道姆", "rating": 9.4, "tags": ["动物", "忠诚", "感动"]},
        {"title": "遗愿清单", "year": 2007, "director": "罗伯·莱纳", "rating": 8.7, "tags": ["生命", "友情", "死亡"]},
        {"title": "素媛", "year": 2013, "director": "李俊益", "rating": 9.2, "tags": ["儿童", "创伤", "希望"]},
        {"title": "入殓师", "year": 2008, "director": "泷田洋二郎", "rating": 8.8, "tags": ["生死", "职业", "尊严"]},
        {"title": "重庆森林", "year": 1994, "director": "王家卫", "rating": 8.7, "tags": ["孤独", "都市", "错过"]}
    ]
}

def search_movies(state):
    """基于用户偏好和情绪搜索电影"""
    mood = state.get("mood", "治愈")
    preferences = state.get("user_preferences", {})
    context = state.get("session_context", {})
    
    # 获取基础电影列表
    base_movies = MOVIE_DATABASE.get(mood, MOVIE_DATABASE["治愈"])
    
    # 如果有特定偏好，进行智能筛选
    if preferences or context.get("genre_hints"):
        filtered_movies = filter_movies_by_preferences(base_movies, preferences, context)
    else:
        filtered_movies = base_movies
    
    # 添加一些其他类型的电影作为候选
    if len(filtered_movies) < 3:
        for other_mood, movies in MOVIE_DATABASE.items():
            if other_mood != mood:
                filtered_movies.extend(random.sample(movies, min(2, len(movies))))
    
    state["movie_options"] = filtered_movies[:5]  # 限制为5个选项
    return state

def filter_movies_by_preferences(movies, preferences, context):
    """根据用户偏好筛选电影"""
    filtered = []
    
    genre_hints = context.get("genre_hints", [])
    avoid_list = preferences.get("avoid", [])
    
    for movie in movies:
        # 检查是否包含用户想要避免的元素
        should_skip = False
        for avoid_item in avoid_list:
            if avoid_item.lower() in movie["title"].lower() or avoid_item in movie.get("tags", []):
                should_skip = True
                break
        
        if should_skip:
            continue
            
        # 计算匹配分数
        score = calculate_movie_score(movie, preferences, genre_hints)
        movie["match_score"] = score
        filtered.append(movie)
    
    # 按匹配分数排序
    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return filtered

def calculate_movie_score(movie, preferences, genre_hints):
    """计算电影匹配分数"""
    score = movie.get("rating", 7.0) / 10.0  # 基础评分权重
    
    # 类型匹配加分
    movie_tags = movie.get("tags", [])
    preferred_genres = preferences.get("genres", []) + genre_hints
    
    for genre in preferred_genres:
        if genre in movie_tags:
            score += 0.2
    
    # 导演和演员匹配
    if movie.get("director") in preferences.get("actors", []):
        score += 0.3
    
    return min(score, 1.0)

def get_movie_details(state):
    """获取电影详细信息"""
    selected_movie = state.get("selected_movie", {})
    
    if not selected_movie:
        # 如果没有选择，使用第一个选项
        options = state.get("movie_options", [])
        if options:
            selected_movie = options[0]
            state["selected_movie"] = selected_movie
    
    # 这里可以集成外部API获取更多信息
    # 比如豆瓣API、TMDB等
    enhanced_details = enhance_movie_info(selected_movie)
    state["selected_movie"] = enhanced_details
    
    return state

def enhance_movie_info(movie):
    """增强电影信息（模拟API调用）"""
    # 这里可以添加更多信息
    enhanced = movie.copy()
    
    # 添加一些模拟的额外信息
    enhanced["plot_summary"] = generate_plot_summary(movie)
    enhanced["why_recommend"] = generate_recommendation_reason(movie)
    
    return enhanced

def generate_plot_summary(movie):
    """生成电影剧情简介"""
    summaries = {
        "夏洛特烦恼": "一个中年失意男子在同学聚会上醉酒后，神奇地回到了高中时代，重新开始人生的搞笑故事。",
        "小森林": "一位年轻女孩回到家乡小村庄，通过制作传统料理重新认识生活意义的温暖电影。",
        "灌篮高手": "讲述一群高中生为了篮球梦想而拼搏奋斗的青春热血动画。",
        "你的名字": "两个素不相识的高中生通过神秘的身体交换，跨越时空寻找彼此的浪漫故事。",
        "忠犬八公的故事": "一只忠诚的狗狗在主人去世后仍然每天等待主人归来的感人真实故事。"
    }
    
    return summaries.get(movie["title"], "一部精彩的电影，值得观看。")

def generate_recommendation_reason(movie):
    """生成推荐理由"""
    return f"这部{movie['year']}年的作品，由{movie['director']}导演，评分{movie['rating']}，是一部{'/'.join(movie.get('tags', []))}题材的优秀电影。"

def search_similar_movies(state):
    """搜索相似电影"""
    selected_movie = state.get("selected_movie", {})
    
    if not selected_movie:
        return state
    
    # 基于标签和评分查找相似电影
    similar_movies = []
    selected_tags = set(selected_movie.get("tags", []))
    
    for mood_movies in MOVIE_DATABASE.values():
        for movie in mood_movies:
            if movie["title"] == selected_movie["title"]:
                continue
                
            movie_tags = set(movie.get("tags", []))
            similarity = len(selected_tags & movie_tags) / max(len(selected_tags | movie_tags), 1)
            
            if similarity > 0.3:  # 相似度阈值
                movie["similarity_score"] = similarity
                similar_movies.append(movie)
    
    # 排序并取前3个
    similar_movies.sort(key=lambda x: x["similarity_score"], reverse=True)
    state["similar_movies"] = similar_movies[:3]
    
    return state
