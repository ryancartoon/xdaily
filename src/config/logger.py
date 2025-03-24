import sys
from pathlib import Path
from loguru import logger
from uuid import uuid4
from .settings import settings

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

class CorrelationFilter:
    def __init__(self):
        self.correlation_id = str(uuid4())

    def __call__(self, record):
        record["correlation_id"] = self.correlation_id
        return True

# 移除默认的 logger 配置
logger.remove()

# 配置新的 logger
logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {correlation_id} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            "level": "DEBUG" if settings.ENVIRONMENT == "dev" else "INFO",
            "filter": CorrelationFilter(),
            "diagnose": True,  # 启用异常诊断
            "backtrace": True,  # 显示完整的异常回溯
            "enqueue": True    # 启用异步日志
        },
        {
            "sink": LOG_DIR / "app_{time:YYYY-MM-DD}.log",
            "rotation": "00:00",
            "retention": "30 days",
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {correlation_id} | {name}:{function}:{line} | {message}",
            "level": "DEBUG",
            "compression": "zip",
            "serialize": True,
            "diagnose": True,
            "backtrace": True,
            "enqueue": True
        }
    ]
)

# 添加一个异常处理器
@logger.catch(onerror=lambda _: sys.exit(1))
def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.exit(0)
    
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("Uncaught exception:")

# 设置未捕获异常的处理器
sys.excepthook = handle_exception