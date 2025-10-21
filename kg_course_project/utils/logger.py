# 日志配置
import logging
import sys

# 默认日志级别为 INFO
def get_logger(name, level=logging.INFO):
    """获取一个配置好的 logger"""
    logger = logging.getLogger(name)  # 单例模式，相同名字返回同一实例，不存在则创建
    if not logger.handlers: # 防止重复添加 handler，检查该记录器是否已经配置了处理器
    # 避免在多次调用时重复添加处理器，导致日志重复输出
        logger.setLevel(level) #logging.DEBUG: 显示所有消息；logging.INFO: 显示 INFO 及更高级别；logging.ERROR: 只显示 ERROR 和 CRITICAL
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

'''
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

def get_logger(name, level=logging.INFO, log_to_file=True, log_dir="logs"):
    """
    获取一个配置好的 logger，支持控制台和文件输出
    
    Args:
        name: logger 名称
        level: 日志级别
        log_to_file: 是否保存到文件
        log_dir: 日志文件目录
    """
    logger = logging.getLogger(name)
    
    # 如果logger已经配置过，直接返回（防止重复配置）
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # 1. 控制台处理器（始终启用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)  # 控制台可以使用不同级别
    logger.addHandler(console_handler)
    
    # 2. 文件处理器（可选）
    if log_to_file:
        file_handler = create_file_handler(log_dir, name, level, formatter)
        if file_handler:
            logger.addHandler(file_handler)
    
    return logger

def create_file_handler(log_dir, name, level, formatter):
    """创建文件处理器"""
    try:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 生成带时间戳的日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{name}_{timestamp}.log"
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        
        logger = logging.getLogger(name)
        logger.info(f"日志文件已创建: {log_file}")
        
        return file_handler
        
    except Exception as e:
        print(f"创建日志文件失败: {e}")
        return None

def setup_rotating_logger(name, level=logging.INFO, max_bytes=10*1024*1024, backup_count=5):
    """
    设置带日志轮转的logger（适合生产环境）
    
    Args:
        max_bytes: 单个日志文件最大大小（默认10MB）
        backup_count: 保留的备份文件数量
    """
    import logging.handlers
    
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 创建日志目录
    log_dir = "logs"
    Path(log_dir).mkdir(exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 轮转文件处理器
    log_file = Path(log_dir) / f"{name}.log"
    rotating_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    rotating_handler.setFormatter(formatter)
    logger.addHandler(rotating_handler)
    
    return logger
'''