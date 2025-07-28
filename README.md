# 🎬 MovieCompanion - 智能电影推荐系统

一个基于实时数据和智能分析的电影推荐系统，支持情绪识别和个性化推荐。

## ✨ 核心特性

### 🌐 实时数据获取
- **TMDB API集成**: 获取全球最新电影数据
- **正在热映**: 实时院线电影信息
- **即将上映**: 未来电影预告和上映计划
- **多平台支持**: 支持Douban、Maoyan等数据源

### 🎯 智能推荐
- **情绪分析**: 理解用户当前心情状态
- **个性化过滤**: 根据用户需求筛选推荐
- **多维度分析**: 结合评分、类型、情绪等因素
- **实用建议**: 提供观影环境和时间建议

### 🤖 简洁高效
- **直观交互**: 自然语言对话方式
- **快速响应**: 优化的数据处理流程
- **可靠稳定**: 错误处理和降级机制
- **易于扩展**: 模块化设计，便于功能增强

## 🚀 快速开始

### 1. 环境配置
```bash
# 克隆项目
git clone <your-repo>
cd MovieCompanion

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑 .env 文件，添加你的API密钥
```

### 2. API密钥配置
在 `.env` 文件中配置以下密钥：

```env
# SiliconFlow API (必需，用于AI模型)
OPENAI_API_KEY=sk-your-siliconflow-api-key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# TMDB API (推荐，用于实时电影数据)
TMDB_API_KEY=your-tmdb-api-key

# 可选：其他电影数据源
DOUBAN_API_KEY=your-douban-api-key
MAOYAN_API_KEY=your-maoyan-api-key
```

### 3. 运行程序
```bash
# 启动电影推荐系统
python main.py
```

## 🏗️ 项目结构

```
MovieCompanion/
├── main.py                    # 主程序入口
├── movie_agent.py             # 核心推荐引擎
├── agents/                    # 代理模块
│   ├── realtime_movie_agent.py  # 实时数据获取
│   ├── movie_database_agent.py  # 本地电影数据库
│   └── __init__.py
├── .env.example               # 环境变量模板
├── requirements.txt           # 项目依赖
└── README.md                  # 项目文档
```

## 💡 使用示例

### 基于情绪的推荐
```
👤 您: 我一个人在陌生城市实习，很孤独，有没有最近的好电影推荐

🎬 推荐助手: 
🎬 **当前正在热映的电影推荐：**

1. **《你好,李焕英》**
   - 评分：7.8/10
   - 上映日期：2025-07-15
   - 简介：温暖的亲情喜剧，能带来情感慰藉...

💡 **针对您的情况特别推荐：**
考虑到您一个人在陌生城市，建议选择温暖治愈系的电影，
可以在观影中获得情感慰藉和心灵放松。
```

### 获取最新电影
```
👤 您: 最近有什么好看的电影？

🎬 推荐助手:
🎬 **当前正在热映的电影推荐：**

1. **《封神第二部》**
   - 评分：8.2/10
   - 上映日期：2025-07-20
   - 简介：国产奇幻大片，视觉效果震撼...
```

## 🔧 核心功能

### 实时数据获取
- 自动获取TMDB最新电影数据
- 支持多种查询模式（热映、即将上映、搜索）
- 智能数据过滤和本地化处理

### 情绪识别与分析
- 关键词提取：识别用户情绪状态
- 上下文理解：分析观影场景需求
- 个性化匹配：基于情绪推荐合适影片

### 推荐引擎
- 多维度评分：结合评分、类型、情绪适配度
- 动态排序：根据用户偏好调整推荐顺序
- 详细说明：提供推荐理由和观影建议

## 🎛️ 配置选项

### 模型配置
```python
# 在 movie_database_agent.py 中配置AI模型
MODEL_NAME = "Qwen/Qwen3-8B"  # 可更换为其他兼容模型
TEMPERATURE = 0.4             # 控制回答创造性
```

### API配置
```python
# 在 realtime_movie_agent.py 中配置数据源
TMDB_BASE_URL = "https://api.themoviedb.org/3"
LANGUAGE = "zh-CN"            # 语言设置
REGION = "CN"                 # 地区设置
```

## 📊 支持的数据源

| 数据源 | 功能 | 状态 |
|--------|------|------|
| TMDB | 国际电影数据、评分、海报 | ✅ 支持 |
| 本地数据库 | 精选电影、情绪标签 | ✅ 支持 |
| Douban | 中文电影评分、评论 | 🔄 开发中 |
| Maoyan | 国内票房、排片数据 | 🔄 开发中 |

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境
```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black .
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 常见问题

### Q: 如何获取TMDB API密钥？
A: 访问 [TMDB官网](https://www.themoviedb.org/settings/api) 注册账号并申请API密钥。

### Q: 为什么有些电影没有中文信息？
A: TMDB主要面向国际市场，部分中文信息可能不完整。我们正在集成更多中文数据源。

### Q: 如何添加自定义电影数据？
A: 编辑 `agents/movie_database_agent.py` 中的 `MOVIE_DATABASE` 字典，添加您的电影数据。

### Q: 系统支持哪些情绪识别？
A: 目前支持：孤独、治愈、压力、开心、悲伤等基本情绪，更多情绪类型正在开发中。

---

🎬 **享受您的观影时光！** 如果遇到问题，请随时提交Issue。
TMDB_API_KEY=your-tmdb-api-key

# 地理配置
DEFAULT_CITY=北京
DEFAULT_LANGUAGE=zh-CN
```

#### 获取API密钥：
- **SiliconFlow**: [注册账号](https://cloud.siliconflow.cn/) 获取免费API密钥
- **TMDB**: [申请API密钥](https://www.themoviedb.org/settings/api) (免费)

### 3. 运行Agent
```bash
python agent_main.py
```

## 🏗️ 项目结构

```
MovieCompanion/
├── agent_main.py              # 主程序入口
├── agents/
│   ├── intelligent_agent.py   # 智能推荐Agent
│   ├── realtime_movie_agent.py# 实时数据Agent
│   └── movie_database_agent.py# 本地电影数据库
├── .env.example               # 环境配置模板
├── requirements.txt           # 依赖包
└── README.md                  # 项目说明
```

## 🛠️ 核心组件

### IntelligentAgent (智能推荐Agent)
主要的电影推荐Agent，具备：
- 11个专业工具（情绪分析、个性化搜索、实时数据等）
- 自主决策和策略调整
- 用户画像学习和记忆系统
- 创造性问题解决

### RealTimeMovieDataAgent (实时数据Agent)
负责获取最新电影数据：
- TMDB API集成
- 正在热映电影
- 电影搜索和详情
- 即将上映预告
- 排片信息（模拟）

### MovieDatabaseAgent (本地数据库)
提供基础电影数据和分类：
- 按情绪分类的电影库
- 经典电影推荐
- 离线数据支持

## 🎯 使用示例

### 基础对话
```python
from agents.intelligent_agent import MovieRecommendationAgent

agent = MovieRecommendationAgent()

# 基于情绪推荐
response = agent.chat("我今天心情不好，想看点治愈的电影")

# 获取最新电影
response = agent.chat("最近有什么好看的电影？")

# 搜索特定电影
response = agent.chat("帮我查一下《流浪地球》的信息")
```

### 直接API调用
```python
from agents.realtime_movie_agent import RealTimeMovieDataAgent

# 获取实时数据
realtime_agent = RealTimeMovieDataAgent()
movies = realtime_agent.get_now_playing_movies()
print(f"获取到 {len(movies)} 部正在热映的电影")
```

## 🔧 配置说明

### 环境变量
- `OPENAI_API_KEY`: SiliconFlow API密钥（必需）
- `OPENAI_BASE_URL`: API基础URL
- `TMDB_API_KEY`: TMDB电影数据库API密钥
- `DEFAULT_CITY`: 默认城市（用于本地化）
- `DEFAULT_LANGUAGE`: 默认语言

### 网络测试
```bash
# 测试TMDB API连接
python -c "import requests; print('TMDB API状态:', requests.get('https://api.themoviedb.org/3/configuration', timeout=5).status_code)"
```

## 🌟 Agent vs 工作流

### 🤖 真正的Agent特征
- **自主性**: 能够设定目标和制定计划
- **反应性**: 感知环境变化并作出响应
- **主动性**: 主动发现需求和机会
- **社交性**: 与用户建立长期互动关系

### 📋 传统工作流特征
- 固定的步骤序列
- 预定义的决策路径
- 被动响应模式
- 无学习能力

## 📊 技术架构

```
用户输入 → 情绪分析 → 目标设定 → 工具选择 → 数据获取 → 个性化处理 → 推荐生成 → 反馈学习
```

### 关键技术
- **LangChain**: Agent框架和工具管理
- **OpenAI函数调用**: 智能工具选择
- **TMDB API**: 实时电影数据
- **自然语言处理**: 情绪和需求分析

## 🚧 扩展功能

### 即将支持
- [ ] 购票链接集成（猫眼、淘票票）
- [ ] 影院位置服务
- [ ] 多语言支持
- [ ] 移动端API

### 高级功能
- [ ] 群组推荐（家庭/朋友）
- [ ] 观影社区
- [ ] 个人观影历史
- [ ] 智能提醒系统

## 🐛 故障排除

### 常见问题
1. **API密钥错误**: 检查 `.env` 文件配置
2. **网络连接**: 确认能访问TMDB API
3. **依赖问题**: 重新安装requirements.txt

### 错误诊断
```bash
# 检查环境变量
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('TMDB_API_KEY')[:10] + '...' if os.getenv('TMDB_API_KEY') else 'Not set')"

# 测试Agent初始化
python -c "from agents.intelligent_agent import MovieRecommendationAgent; agent = MovieRecommendationAgent(); print('Agent初始化成功')"
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issues和Pull Requests！

---

**MovieCompanion - 让AI成为你的专属观影顾问** 🎬✨
