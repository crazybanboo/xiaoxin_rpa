"""
企业微信半自动化主控制器
整合所有子模块，提供统一的API接口
"""
import os
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from ...core.locator import CompositeLocator
from ...core.mouse import MouseController
from ...core.keyboard import KeyboardController
from ...core.wechat_detector import WechatProcessDetector, ProcessInfo
from ...core.utils import logger, config, RpaException
from .wechat_operations import WechatOperationInterface, OperationResult
from .exceptions import WechatNotFoundError, WechatWindowError, WechatOperationError


class WechatHalfAuto:
    """企业微信半自动化主控制器"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        初始化主控制器
        
        Args:
            config_override: 配置覆盖项
        """
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = self._load_config(config_override)
        
        # 初始化组件
        self.process_detector = WechatProcessDetector()
        self.locator = CompositeLocator()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.operation_interface = WechatOperationInterface(
            self.locator, self.mouse, self.keyboard, self.config
        )
        
        # 状态变量
        self.current_process: Optional[ProcessInfo] = None
        self.current_window_info: Optional[Dict[str, Any]] = None
        self.is_initialized = False
        
    def _load_config(self, config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            'wechat': {
                'process_names': ['WXWork.exe', '企业微信.exe'],
                'window_detection_timeout': 10.0,
                'operation_delay': 0.5,
                'template_confidence': 0.8,
                'multi_select_interval': 0.2,
                'message_send_delay': 1.0
            },
            'templates': {
                'template_dir': 'templates/wechat',
                'button_templates': {},
                'checkbox_templates': {}
            }
        }
        
        # 从全局配置中获取企业微信配置
        wechat_config = config.get('wechat', {})
        if wechat_config:
            default_config['wechat'].update(wechat_config)
        
        # 应用配置覆盖
        if config_override:
            for key, value in config_override.items():
                if key in default_config:
                    default_config[key].update(value)
                else:
                    default_config[key] = value
        
        return default_config
    
    def initialize(self) -> bool:
        """
        初始化企业微信半自动化系统
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化企业微信半自动化系统...")
            
            # 1. 检测企业微信进程
            self.logger.debug("检测企业微信进程...")
            processes = self.process_detector.find_wechat_processes()
            
            if not processes:
                raise WechatNotFoundError("未找到正在运行的企业微信进程")
            
            # 选择主进程
            self.current_process = self.process_detector.get_main_wechat_process()
            if not self.current_process:
                raise WechatNotFoundError("无法确定主要的企业微信进程")
            
            self.logger.info(f"找到企业微信进程: PID={self.current_process.pid}, 名称={self.current_process.name}")
            
            # 2. 获取窗口信息
            self.logger.debug("获取企业微信窗口信息...")
            window_handle = self.process_detector.get_process_window_handle(self.current_process.pid)
            
            if not window_handle:
                raise WechatWindowError("无法获取企业微信窗口句柄")
            
            window_info = self.locator.window_locator.get_window_info(window_handle)
            if not window_info:
                raise WechatWindowError("无法获取企业微信窗口信息")
            
            # 检查窗口是否为有效的主窗口（避免获取到1x1的后台窗口）
            if window_info.width <= 100 or window_info.height <= 100:
                raise WechatWindowError(
                    f"检测到的企业微信窗口太小 ({window_info.width}x{window_info.height})，"
                    "可能是后台窗口。请确保企业微信主窗口已打开并可见。"
                )
            
            self.current_window_info = {
                'hwnd': window_info.hwnd,
                'title': window_info.title,
                'rect': window_info.rect,
                'width': window_info.width,
                'height': window_info.height,
                'center': window_info.center,
                'is_visible': window_info.is_visible
            }
            
            self.logger.info(f"企业微信窗口信息: {window_info.title}, 大小: {window_info.width}x{window_info.height}")
            
            # 3. 验证模板目录
            template_dir = Path(self.config['templates']['template_dir'])
            if not template_dir.exists():
                self.logger.warning(f"模板目录不存在: {template_dir}")
                template_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"已创建模板目录: {template_dir}")
            
            self.is_initialized = True
            self.logger.info("企业微信半自动化系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            self.is_initialized = False
            return False
    
    def get_wechat_window_info(self) -> Optional[Dict[str, Any]]:
        """
        获取企业微信窗口信息
        
        Returns:
            Dict[str, Any]: 窗口信息字典
        """
        if not self.is_initialized:
            self.logger.error("系统未初始化")
            return None
        
        return self.current_window_info
    
    def get_locator(self) -> CompositeLocator:
        """获取定位器实例"""
        return self.locator
    
    def get_image_recognizer(self):
        """获取图像识别器"""
        return self.locator.image_locator
    
    def get_mouse_controller(self) -> MouseController:
        """获取鼠标控制器"""
        return self.mouse
    
    def get_keyboard_controller(self) -> KeyboardController:
        """获取键盘控制器"""
        return self.keyboard
    
    def get_operation_interface(self) -> WechatOperationInterface:
        """获取操作接口"""
        return self.operation_interface
    
    def execute_multi_chat_send(self, message: str, chat_templates: List[str]) -> OperationResult:
        """
        执行多聊天发送消息
        
        Args:
            message: 要发送的消息
            chat_templates: 聊天模板路径列表
            
        Returns:
            OperationResult: 操作结果
        """
        if not self.is_initialized:
            return OperationResult(
                success=False,
                message="系统未初始化",
                error_code="NOT_INITIALIZED"
            )
        
        try:
            self.logger.info(f"开始执行多聊天发送任务，消息: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # 检查模板文件是否存在
            template_dir = Path(self.config['templates']['template_dir'])
            valid_templates = []
            
            for template_path in chat_templates:
                if not os.path.isabs(template_path):
                    full_path = template_dir / template_path
                else:
                    full_path = Path(template_path)
                
                if full_path.exists():
                    valid_templates.append(str(full_path))
                else:
                    self.logger.warning(f"模板文件不存在: {full_path}")
            
            if not valid_templates:
                return OperationResult(
                    success=False,
                    message="没有找到有效的模板文件",
                    error_code="NO_VALID_TEMPLATES"
                )
            
            # 执行多聊天发送
            result = self.operation_interface.execute_send_to_multiple_chats(message, valid_templates)
            
            self.logger.info(f"多聊天发送任务完成，结果: {result.message}")
            return result
            
        except Exception as e:
            self.logger.error(f"执行多聊天发送失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error_code="EXECUTION_ERROR"
            )
    
    def find_and_click_button(self, template_path: str, confidence: Optional[float] = None) -> OperationResult:
        """
        查找并点击按钮
        
        Args:
            template_path: 模板路径
            confidence: 置信度
            
        Returns:
            OperationResult: 操作结果
        """
        if not self.is_initialized:
            return OperationResult(
                success=False,
                message="系统未初始化",
                error_code="NOT_INITIALIZED"
            )
        
        try:
            # 查找按钮
            find_result = self.operation_interface.find_button_by_template(template_path, confidence)
            if not find_result.success:
                return find_result
            
            # 点击按钮
            if find_result.data and "position" in find_result.data:
                position = find_result.data["position"]
                click_result = self.operation_interface.click_at_position(position[0], position[1])
                return click_result
            else:
                return OperationResult(
                    success=False,
                    message="无法获取按钮位置",
                    error_code="NO_BUTTON_POSITION"
                )
                
        except Exception as e:
            self.logger.error(f"查找并点击按钮失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"操作失败: {str(e)}",
                error_code="BUTTON_CLICK_ERROR"
            )
    
    def send_message_to_current_chat(self, message: str) -> OperationResult:
        """
        向当前聊天发送消息
        
        Args:
            message: 要发送的消息
            
        Returns:
            OperationResult: 操作结果
        """
        if not self.is_initialized:
            return OperationResult(
                success=False,
                message="系统未初始化",
                error_code="NOT_INITIALIZED"
            )
        
        try:
            # 输入消息
            type_result = self.operation_interface.type_message(message)
            if not type_result.success:
                return type_result
            
            # 发送消息
            send_result = self.operation_interface.send_message()
            return send_result
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"发送消息失败: {str(e)}",
                error_code="SEND_MESSAGE_ERROR"
            )
    
    def take_screenshot(self, filename: Optional[str] = None) -> OperationResult:
        """
        截取操作截图
        
        Args:
            filename: 截图文件名
            
        Returns:
            OperationResult: 操作结果
        """
        return self.operation_interface.take_operation_screenshot(filename)
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理企业微信半自动化系统资源...")
        self.is_initialized = False
        self.current_process = None
        self.current_window_info = None
        self.logger.info("资源清理完成")


def main():
    """主函数 - 演示使用"""
    print("企业微信半自动化系统演示")
    print("=" * 50)
    
    # 创建主控制器实例
    wechat_auto = WechatHalfAuto()
    
    try:
        # 初始化系统
        if not wechat_auto.initialize():
            print("❌ 系统初始化失败")
            return
        
        print("✅ 系统初始化成功")
        
        # 获取窗口信息
        window_info = wechat_auto.get_wechat_window_info()
        if window_info:
            print(f"📱 企业微信窗口: {window_info['title']}")
            print(f"📏 窗口大小: {window_info['width']}x{window_info['height']}")
        
        # 演示截图功能
        print("\n📸 正在截取操作截图...")
        screenshot_result = wechat_auto.take_screenshot()
        if screenshot_result.success and screenshot_result.data:
            print(f"✅ 截图成功: {screenshot_result.data['screenshot_path']}")
        else:
            print(f"❌ 截图失败: {screenshot_result.message}")
    
        # 演示发送消息功能
        print("\n💬 演示发送消息功能...")
        test_message = "这是一条测试消息"
        
        # 注意：这里需要实际的模板文件才能工作
        # test_templates = ['chat1.png', 'chat2.png']
        # result = wechat_auto.execute_multi_chat_send(test_message, test_templates)
        # print(f"发送结果: {result.message}")
        
        print("💡 提示：要使用完整功能，请准备聊天模板图片并放置在 templates/wechat/ 目录下")
        
    except Exception as e:
        print(f"❌ 运行时错误: {str(e)}")
        
    finally:
        # 清理资源
        wechat_auto.cleanup()
        print("\n🔧 系统清理完成")


if __name__ == "__main__":
    main()