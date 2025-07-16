"""
RPA Framework 配置管理模块
提供全局配置管理和设置功能

重构改进：
1. 增加环境变量支持
2. 运行时配置更新
3. 配置监听和回调机制
4. 更灵活的配置访问接口
"""

import os
import time
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict, field


@dataclass
class GeneralSettings:
    """通用设置"""
    screenshot_dir: str = "logs/screenshots"
    template_dir: str = "templates"
    default_timeout: float = 10.0
    retry_count: int = 3
    retry_delay: float = 1.0
    debug_mode: bool = False


@dataclass
class MouseSettings:
    """鼠标操作设置"""
    move_duration: float = 0.5
    click_delay: float = 0.1
    double_click_interval: float = 0.1
    scroll_speed: int = 3
    fail_safe: bool = True


@dataclass
class KeyboardSettings:
    """键盘操作设置"""
    type_interval: float = 0.05
    key_delay: float = 0.1
    pause_after_type: float = 0.1
    auto_shift: bool = True


@dataclass
class ImageSettings:
    """图像识别设置"""
    confidence: float = 0.8
    grayscale: bool = True
    region: Optional[tuple] = None
    template_matching_method: str = "TM_CCOEFF_NORMED"
    scale_range: tuple = (0.8, 1.2)
    scale_step: float = 0.1


@dataclass
class WindowSettings:
    """窗口操作设置"""
    activate_timeout: float = 5.0
    window_search_timeout: float = 10.0
    min_window_size: tuple = (100, 100)
    default_window_state: str = "normal"  # normal, maximized, minimized


@dataclass
class LoggingSettings:
    """日志设置"""
    level: str = "DEBUG"  # 默认显示所有等级日志
    max_file_size: str = "10MB"
    backup_count: int = 5
    log_format: str = "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
    console_format: str = "%(log_color)s%(asctime)s [%(levelname)s] [%(name)s] %(caller_file)s:%(caller_line)d - %(message)s"
    date_format: str = "%H:%M:%S"
    enable_master_log: bool = True  # 启用总日志文件
    master_log_format: str = "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"


@dataclass
class SecuritySettings:
    """安全设置"""
    enable_fail_safe: bool = True
    fail_safe_corner: str = "top-left"  # top-left, top-right, bottom-left, bottom-right
    max_operation_time: float = 300.0  # 最大操作时间（秒）
    screenshot_on_error: bool = True
    sensitive_data_mask: bool = True


@dataclass
class WechatSettings:
    """企业微信设置"""
    process_names: List[str] = field(default_factory=lambda: ["WXWork.exe", "企业微信.exe", "WeChatWork.exe", "wxwork.exe"])
    window_detection_timeout: float = 10.0
    operation_delay: float = 0.5
    template_confidence: float = 0.8
    multi_select_interval: float = 0.2
    message_send_delay: float = 1.0
    max_retry_count: int = 3
    screenshot_on_operation: bool = True
    # 窗口配置
    window_size: Dict[str, int] = field(default_factory=lambda: {"width": 1200, "height": 800})
    window_position: Dict[str, int] = field(default_factory=lambda: {"x": 100, "y": 100})
    # 疯狂连点配置
    crazy_click_settings: Dict[str, Any] = field(default_factory=lambda: {
        "clicks_per_group": 100,     # 每组连点次数
        "group_interval": 2.0,       # 组间隔时间（秒）
        "total_groups": 6,           # 总组数
        "click_interval": 0.01       # 单次点击间隔
    })

class Settings:
    """RPA框架配置管理器 - 重构版本"""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        self.config_file = project_root / config_file
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 配置变更回调列表
        self._change_callbacks: List[Callable[[str, str, Any], None]] = []
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 环境变量前缀
        self.env_prefix = "RPA_"
        
        # 初始化各个配置组
        self.general = GeneralSettings()
        self.mouse = MouseSettings()
        self.keyboard = KeyboardSettings()
        self.image = ImageSettings()
        self.window = WindowSettings()
        self.logging = LoggingSettings()
        self.security = SecuritySettings()
        self.wechat = WechatSettings()
        
        self.load_config()
    
    def load_config(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                # 更新各个配置组
                if 'general' in config_data:
                    self._update_dataclass(self.general, config_data['general'])
                if 'mouse' in config_data:
                    self._update_dataclass(self.mouse, config_data['mouse'])
                if 'keyboard' in config_data:
                    self._update_dataclass(self.keyboard, config_data['keyboard'])
                if 'image' in config_data:
                    self._update_dataclass(self.image, config_data['image'])
                if 'window' in config_data:
                    self._update_dataclass(self.window, config_data['window'])
                if 'logging' in config_data:
                    self._update_dataclass(self.logging, config_data['logging'])
                if 'security' in config_data:
                    self._update_dataclass(self.security, config_data['security'])
                if 'wechat' in config_data:
                    self._update_dataclass(self.wechat, config_data['wechat'])
                    
            except Exception as e:
                print(f"警告: 加载配置文件失败，使用默认配置: {e}")
        else:
            # 首次运行，创建默认配置文件
            self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'general': asdict(self.general),
            'mouse': asdict(self.mouse),
            'keyboard': asdict(self.keyboard),
            'image': asdict(self.image),
            'window': asdict(self.window),
            'logging': asdict(self.logging),
            'security': asdict(self.security),
            'wechat': asdict(self.wechat),
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """更新数据类对象的属性"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'general': asdict(self.general),
            'mouse': asdict(self.mouse),
            'keyboard': asdict(self.keyboard),
            'image': asdict(self.image),
            'window': asdict(self.window),
            'logging': asdict(self.logging),
            'security': asdict(self.security),
            'wechat': asdict(self.wechat),
        }
    
    def update_settings(self, section: str, **kwargs):
        """更新指定配置节的设置"""
        if section == 'general':
            for key, value in kwargs.items():
                if hasattr(self.general, key):
                    setattr(self.general, key, value)
        elif section == 'mouse':
            for key, value in kwargs.items():
                if hasattr(self.mouse, key):
                    setattr(self.mouse, key, value)
        elif section == 'keyboard':
            for key, value in kwargs.items():
                if hasattr(self.keyboard, key):
                    setattr(self.keyboard, key, value)
        elif section == 'image':
            for key, value in kwargs.items():
                if hasattr(self.image, key):
                    setattr(self.image, key, value)
        elif section == 'window':
            for key, value in kwargs.items():
                if hasattr(self.window, key):
                    setattr(self.window, key, value)
        elif section == 'logging':
            for key, value in kwargs.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        elif section == 'security':
            for key, value in kwargs.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        elif section == 'wechat':
            for key, value in kwargs.items():
                if hasattr(self.wechat, key):
                    setattr(self.wechat, key, value)
        
        # 保存更新后的配置
        self.save_config()
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.general = GeneralSettings()
        self.mouse = MouseSettings()
        self.keyboard = KeyboardSettings()
        self.image = ImageSettings()
        self.window = WindowSettings()
        self.logging = LoggingSettings()
        self.security = SecuritySettings()
        self.save_config()
    
    def validate_settings(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证通用设置
        if self.general.default_timeout <= 0:
            errors.append("default_timeout 必须大于 0")
        if self.general.retry_count < 0:
            errors.append("retry_count 不能为负数")
        
        # 验证鼠标设置
        if self.mouse.move_duration < 0:
            errors.append("move_duration 不能为负数")
        if self.mouse.click_delay < 0:
            errors.append("click_delay 不能为负数")
        
        # 验证键盘设置
        if self.keyboard.type_interval < 0:
            errors.append("type_interval 不能为负数")
        
        # 验证图像设置
        if not 0 <= self.image.confidence <= 1:
            errors.append("confidence 必须在 0-1 之间")
        
        # 验证安全设置
        if self.security.max_operation_time <= 0:
            errors.append("max_operation_time 必须大于 0")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def add_change_callback(self, callback: Callable[[str, str, Any], None]):
        """
        添加配置变更回调函数
        
        Args:
            callback: 回调函数，参数为 (section, key, new_value)
        """
        with self._lock:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, str, Any], None]):
        """移除配置变更回调函数"""
        with self._lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)
    
    def _notify_change(self, section: str, key: str, value: Any):
        """通知配置变更"""
        with self._lock:
            for callback in self._change_callbacks:
                try:
                    callback(section, key, value)
                except Exception as e:
                    print(f"配置变更回调执行失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        通过点分隔路径获取配置值
        
        Args:
            key: 配置键，支持 'section.key' 格式
            default: 默认值
            
        Returns:
            配置值
            
        Example:
            settings.get('image.confidence', 0.8)
            settings.get('wechat.window_size.width', 1200)
        """
        with self._lock:
            try:
                parts = key.split('.')
                if len(parts) < 2:
                    return default
                
                section_name = parts[0]
                section = getattr(self, section_name, None)
                if section is None:
                    return default
                
                # 如果是dataclass，转换为字典
                if hasattr(section, '__dataclass_fields__'):
                    section_dict = asdict(section)
                else:
                    section_dict = section
                
                # 遍历嵌套路径
                current = section_dict
                for part in parts[1:]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return default
                
                return current
                
            except Exception:
                return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        通过点分隔路径设置配置值
        
        Args:
            key: 配置键，支持 'section.key' 格式
            value: 配置值
            save: 是否立即保存到文件
            
        Returns:
            是否设置成功
            
        Example:
            settings.set('image.confidence', 0.9)
            settings.set('wechat.window_size.width', 1400)
        """
        with self._lock:
            try:
                parts = key.split('.')
                if len(parts) < 2:
                    return False
                
                section_name = parts[0]
                section = getattr(self, section_name, None)
                if section is None:
                    return False
                
                # 如果只有两级，直接设置属性
                if len(parts) == 2:
                    attr_name = parts[1]
                    if hasattr(section, attr_name):
                        setattr(section, attr_name, value)
                        self._notify_change(section_name, attr_name, value)
                        if save:
                            self.save_config()
                        return True
                    return False
                
                # 处理嵌套配置
                current = section
                for part in parts[1:-1]:
                    if hasattr(current, part):
                        current = getattr(current, part)
                    else:
                        return False
                
                # 设置最终值
                final_key = parts[-1]
                if isinstance(current, dict):
                    current[final_key] = value
                elif hasattr(current, final_key):
                    setattr(current, final_key, value)
                else:
                    return False
                
                self._notify_change(section_name, '.'.join(parts[1:]), value)
                if save:
                    self.save_config()
                return True
                
            except Exception as e:
                print(f"设置配置失败: {e}")
                return False
    
    def load_from_env(self):
        """从环境变量加载配置"""
        with self._lock:
            env_mappings = {
                f"{self.env_prefix}IMAGE_CONFIDENCE": "image.confidence",
                f"{self.env_prefix}MOUSE_MOVE_DURATION": "mouse.move_duration",
                f"{self.env_prefix}DEBUG_MODE": "general.debug_mode",
                f"{self.env_prefix}LOG_LEVEL": "logging.level",
                f"{self.env_prefix}WECHAT_CONFIDENCE": "wechat.template_confidence",
                f"{self.env_prefix}WINDOW_WIDTH": "wechat.window_size.width",
                f"{self.env_prefix}WINDOW_HEIGHT": "wechat.window_size.height",
            }
            
            for env_key, config_key in env_mappings.items():
                env_value = os.environ.get(env_key)
                if env_value is not None:
                    # 类型转换
                    try:
                        if config_key.endswith(('.confidence', '.duration', '.delay', '.timeout')):
                            value = float(env_value)
                        elif config_key.endswith(('.width', '.height', '.count', '.size')):
                            value = int(env_value)
                        elif config_key.endswith('.debug_mode'):
                            value = env_value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            value = env_value
                        
                        self.set(config_key, value, save=False)
                        print(f"从环境变量加载配置: {config_key} = {value}")
                        
                    except ValueError as e:
                        print(f"环境变量类型转换失败: {env_key} = {env_value}, 错误: {e}")
    
    def get_section_dict(self, section_name: str) -> Dict[str, Any]:
        """
        获取指定配置节的字典表示
        
        Args:
            section_name: 配置节名称
            
        Returns:
            配置节字典
        """
        with self._lock:
            section = getattr(self, section_name, None)
            if section is None:
                return {}
            
            if hasattr(section, '__dataclass_fields__'):
                return asdict(section)
            return section
    
    def update_section_from_dict(self, section_name: str, data: Dict[str, Any], save: bool = True):
        """
        从字典更新配置节
        
        Args:
            section_name: 配置节名称
            data: 数据字典
            save: 是否保存
        """
        with self._lock:
            section = getattr(self, section_name, None)
            if section is None:
                return
            
            for key, value in data.items():
                if hasattr(section, key):
                    old_value = getattr(section, key)
                    if old_value != value:
                        setattr(section, key, value)
                        self._notify_change(section_name, key, value)
            
            if save:
                self.save_config()
    
    def create_runtime_override(self, **overrides) -> 'RuntimeSettings':
        """
        创建运行时配置覆盖
        
        Args:
            **overrides: 配置覆盖项
            
        Returns:
            运行时配置对象
        """
        return RuntimeSettings(self, overrides)
    
    def export_config(self, export_path: Optional[str] = None) -> str:
        """
        导出配置到文件
        
        Args:
            export_path: 导出路径，None表示使用默认路径
            
        Returns:
            导出文件路径
        """
        if export_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_path = f"config_backup_{timestamp}.yaml"
        
        export_file = Path(export_path)
        with self._lock:
            config_data = self.get_all_settings()
            try:
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                return str(export_file)
            except Exception as e:
                raise Exception(f"导出配置失败: {e}")

    def update_wechat_window_config(self, width: int, height: int, x: int, y: int) -> bool:
        """
        更新企业微信窗口配置（只更新窗口相关配置，保持其他配置不变）
        
        Args:
            width: 窗口宽度
            height: 窗口高度
            x: 窗口x坐标
            y: 窗口y坐标
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 首先更新内存中的配置
            self.wechat.window_size = {"width": width, "height": height}
            self.wechat.window_position = {"x": x, "y": y}
            
            # 读取现有的YAML文件内容
            if not self.config_file.exists():
                # 如果文件不存在，使用完整保存
                self.save_config()
                print(f"✅ 企业微信窗口配置已创建: 大小({width}x{height}), 位置({x}, {y})")
                return True
            
            # 读取现有配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # 确保wechat节存在
            if 'wechat' not in config_data:
                config_data['wechat'] = {}
            
            # 只更新窗口相关配置
            config_data['wechat']['window_size'] = {"width": width, "height": height}
            config_data['wechat']['window_position'] = {"x": x, "y": y}
            
            # 写回文件，使用相同的格式选项
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2, sort_keys=False)
            
            print(f"✅ 企业微信窗口配置已更新: 大小({width}x{height}), 位置({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 更新企业微信窗口配置失败: {str(e)}")
            return False
    
    def get_wechat_window_config(self) -> Dict[str, Dict[str, int]]:
        """
        获取企业微信窗口配置
        
        Returns:
            Dict: 包含window_size和window_position的字典
        """
        return {
            "window_size": self.wechat.window_size,
            "window_position": self.wechat.window_position
        }

    def get_crazy_click_config(self) -> Dict[str, Any]:
        """
        获取疯狂连点配置
        
        Returns:
            Dict: 疯狂连点配置字典
        """
        return self.wechat.crazy_click_settings

    def validate_crazy_click_settings(self) -> bool:
        """
        验证疯狂连点配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        errors = []
        config = self.wechat.crazy_click_settings
        
        # 验证每组连点次数
        if config.get('clicks_per_group', 0) <= 0:
            errors.append("clicks_per_group 必须大于 0")
        
        # 验证组间隔时间
        if config.get('group_interval', 0) < 0:
            errors.append("group_interval 不能为负数")
        
        # 验证总组数
        if config.get('total_groups', 0) <= 0:
            errors.append("total_groups 必须大于 0")
        
        # 验证单次点击间隔
        if config.get('click_interval', 0) < 0:
            errors.append("click_interval 不能为负数")
        
        if errors:
            print("疯狂连点配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


class RuntimeSettings:
    """运行时配置覆盖器"""
    
    def __init__(self, base_settings: Settings, overrides: Dict[str, Any]):
        self.base_settings = base_settings
        self.overrides = overrides
        self._active = True
    
    def __enter__(self):
        """进入上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self._active = False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，优先使用覆盖值"""
        if self._active and key in self.overrides:
            return self.overrides[key]
        return self.base_settings.get(key, default)
    
    def set_override(self, key: str, value: Any):
        """设置覆盖值"""
        if self._active:
            self.overrides[key] = value
    
    def clear_override(self, key: str):
        """清除覆盖值"""
        if self._active and key in self.overrides:
            del self.overrides[key]
    
    def is_active(self) -> bool:
        """检查是否激活"""
        return self._active


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取全局配置实例"""
    return settings


def reload_settings():
    """重新加载配置"""
    global settings
    settings.load_config()


def save_current_settings():
    """保存当前配置"""
    settings.save_config()


def get_config(key: str, default: Any = None) -> Any:
    """便捷的配置获取函数"""
    return settings.get(key, default)


def set_config(key: str, value: Any, save: bool = True) -> bool:
    """便捷的配置设置函数"""
    return settings.set(key, value, save)


def with_config_override(**overrides) -> RuntimeSettings:
    """
    创建临时配置覆盖上下文
    
    Usage:
        with with_config_override(image_confidence=0.9):
            # 在这个代码块中，图像置信度会被临时设置为0.9
            find_and_click("button.png")
    """
    return settings.create_runtime_override(**overrides)


if __name__ == "__main__":
    # 测试配置管理
    print("RPA框架配置管理测试")
    print(f"配置文件: {settings.config_file}")
    print(f"截图目录: {settings.general.screenshot_dir}")
    print(f"鼠标移动时间: {settings.mouse.move_duration}")
    print(f"图像识别置信度: {settings.image.confidence}")
    print(f"配置验证结果: {settings.validate_settings()}") 