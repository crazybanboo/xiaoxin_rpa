"""
RPA Framework 基础工具函数模块
提供截图、日志、配置管理和异常处理等基础功能
"""

import os
import sys
import time
import json
import yaml
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import cv2
import numpy as np
import pyautogui
from PIL import Image
import colorlog


class RpaException(Exception):
    """RPA框架自定义异常类"""
    def __init__(self, message: str, error_code: str = "RPA_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class RpaLogger:
    """日志管理器"""
    
    _instances = {}  # 单例模式存储实例
    
    def __init__(self, name: str = "RPA", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logger()
    
    @classmethod
    def get_logger(cls, name: str = "RPA", log_dir: str = "logs") -> 'RpaLogger':
        """获取日志器实例（单例模式）"""
        if name not in cls._instances:
            cls._instances[name] = cls(name, log_dir)
        return cls._instances[name]
    
    def _setup_logger(self):
        """设置日志器"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 控制台处理器（彩色输出）
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
        
        # 文件处理器
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """严重错误日志"""
        self.logger.critical(message)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        self._config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                raise RpaException(f"加载配置文件失败: {e}", "CONFIG_LOAD_ERROR")
        else:
            # 创建默认配置
            self._config = self._get_default_config()
            self.save_config()
        
        return self._config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            raise RpaException(f"保存配置文件失败: {e}", "CONFIG_SAVE_ERROR")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'general': {
                'screenshot_dir': 'logs/screenshots',
                'template_dir': 'templates',
                'default_timeout': 10,
                'retry_count': 3,
                'retry_delay': 1.0
            },
            'mouse': {
                'move_duration': 0.5,
                'click_delay': 0.1,
                'double_click_interval': 0.1
            },
            'keyboard': {
                'type_interval': 0.05,
                'key_delay': 0.1
            },
            'image': {
                'confidence': 0.8,
                'grayscale': True,
                'region': None
            },
            'logging': {
                'level': 'INFO',
                'max_file_size': '10MB',
                'backup_count': 5
            }
        }


class ScreenCapture:
    """屏幕截图工具"""
    
    def __init__(self, screenshot_dir: str = "logs/screenshots"):
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, 
                  filename: Optional[str] = None) -> str:
        """
        截取屏幕截图
        
        Args:
            region: 截图区域 (left, top, width, height)
            filename: 保存文件名，不指定则自动生成
            
        Returns:
            截图文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                filename = f"screenshot_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(filepath)
            return str(filepath)
            
        except Exception as e:
            raise RpaException(f"截图失败: {e}", "SCREENSHOT_ERROR")
    
    def screenshot_region(self, left: int, top: int, width: int, height: int, 
                         filename: Optional[str] = None) -> str:
        """截取指定区域"""
        return self.screenshot(region=(left, top, width, height), filename=filename)
    
    def screenshot_element(self, element_box: Tuple[int, int, int, int], 
                          filename: Optional[str] = None) -> str:
        """截取元素区域"""
        left, top, right, bottom = element_box
        width = right - left
        height = bottom - top
        return self.screenshot_region(left, top, width, height, filename)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: RpaLogger):
        self.logger = logger
    
    def handle_exception(self, func):
        """异常处理装饰器"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RpaException as e:
                self.logger.error(f"RPA异常: {e.error_code} - {e.message}")
                raise
            except Exception as e:
                error_msg = f"未知异常: {str(e)}"
                self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                raise RpaException(error_msg, "UNKNOWN_ERROR")
        return wrapper
    
    def safe_execute(self, func, *args, **kwargs):
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"执行失败: {str(e)}")
            return None


# 全局实例
logger = RpaLogger.get_logger()
config = ConfigManager()
screen_capture = ScreenCapture()
error_handler = ErrorHandler(logger)


def get_screen_size() -> Tuple[int, int]:
    """获取屏幕尺寸"""
    return pyautogui.size()


def wait_time(seconds: float):
    """等待指定时间"""
    time.sleep(seconds)


def ensure_directory(path: str):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_json(filepath: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RpaException(f"加载JSON文件失败: {e}", "JSON_LOAD_ERROR")


def save_json(data: Dict[str, Any], filepath: str):
    """保存JSON文件"""
    try:
        ensure_directory(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise RpaException(f"保存JSON文件失败: {e}", "JSON_SAVE_ERROR")


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_file_timestamp() -> str:
    """获取适用于文件名的时间戳"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


if __name__ == "__main__":
    # 测试代码
    logger.info("RPA工具模块测试")
    logger.info(f"屏幕尺寸: {get_screen_size()}")
    logger.info(f"配置文件路径: {config.config_file}")
    logger.info(f"截图目录: {screen_capture.screenshot_dir}") 