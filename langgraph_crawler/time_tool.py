"""时间工具 - 获取当前系统时间"""
from datetime import datetime, timezone
import time
from langchain_core.tools import tool

@tool
def get_current_time(format_type: str = "datetime") -> str:
    """获取当前系统时间
    
    这个工具用于获取当前的系统时间信息：
    - 提供多种时间格式选择
    - 支持中文和英文格式
    - 包含详细的时间信息（年月日时分秒）
    - 可用于日志记录、时间戳生成等场景
    
    Args:
        format_type: 时间格式类型
                    - "datetime": 完整日期时间（默认）
                    - "date": 仅日期
                    - "time": 仅时间
                    - "timestamp": Unix时间戳
                    - "chinese": 中文格式
                    - "iso": ISO 8601格式
        
    Returns:
        格式化的时间字符串，根据format_type参数返回不同格式：
        （注意：以下时间仅为示例，返回的是当前系统的本地时间）
        - datetime: "2025-08-04 14:30:25"
        - date: "2025-08-04"
        - time: "14:30:25"
        - timestamp: "1722771025"
        - chinese: "2025年8月4日 14时30分25秒"
        - iso: "2025-08-04T14:30:25+08:00"
        
    使用场景：
    - 为文件添加时间戳
    - 记录操作执行时间
    - 生成报告的创建时间
    - 计算时间间隔
    - 调试和日志记录
    
    注意：返回的是当前系统的本地时间
    """
    try:
        now = datetime.now()
        
        if format_type == "datetime":
            return now.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date":
            return now.strftime("%Y-%m-%d")
        elif format_type == "time":
            return now.strftime("%H:%M:%S")
        elif format_type == "timestamp":
            return str(int(time.time()))
        elif format_type == "chinese":
            return now.strftime("%Y年%m月%d日 %H时%M分%S秒")
        elif format_type == "iso":
            return now.isoformat()
        else:
            # 默认返回完整的datetime格式
            return now.strftime("%Y-%m-%d %H:%M:%S")
            
    except Exception as e:
        return f"获取时间失败: {str(e)}"

@tool
def get_time_info() -> str:
    """获取详细的系统时间信息
    
    这个工具提供完整的时间信息总览：
    - 当前日期和时间
    - 星期几
    - 一年中的第几天
    - Unix时间戳
    - 多种格式的时间表示
    
    Returns:
        包含多种时间格式的详细信息字符串
        
    使用场景：
    - 生成详细的时间报告
    - 系统状态检查
    - 时间调试和分析
    """
    try:
        now = datetime.now()
        
        # 获取星期几（中文）
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday_cn = weekdays[now.weekday()]
        
        # 一年中的第几天
        day_of_year = now.timetuple().tm_yday
        
        time_info = f"""
📅 **当前时间信息**

🕐 **标准格式**: {now.strftime("%Y-%m-%d %H:%M:%S")}
🗓️ **中文格式**: {now.strftime("%Y年%m月%d日 %H时%M分%S秒")}
📆 **星期**: {weekday_cn} ({now.strftime("%A")})
🔢 **今年第几天**: {day_of_year}天
⏰ **Unix时间戳**: {int(time.time())}
🌍 **ISO格式**: {now.isoformat()}
📝 **仅日期**: {now.strftime("%Y-%m-%d")}
🕒 **仅时间**: {now.strftime("%H:%M:%S")}
"""
        return time_info.strip()
        
    except Exception as e:
        return f"获取时间信息失败: {str(e)}"
