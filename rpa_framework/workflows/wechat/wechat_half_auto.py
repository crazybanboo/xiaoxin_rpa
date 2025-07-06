"""
企业微信半自动化主控制器
整合所有子模块，提供统一的API接口

新功能：批量模板匹配和点击
==========================

1. locate_all_by_template() - 批量模板匹配
   - 返回所有匹配的元素位置列表
   - 支持置信度过滤
   - 支持最大结果数量限制
   - 自动去重重叠的匹配项

2. find_and_click_all_buttons() - 批量点击按钮
   - 查找所有匹配的按钮并逐个点击
   - 支持点击间隔时间设置
   - 返回详细的操作结果统计

使用示例：
---------
# 批量定位
results = wechat_auto.get_locator().locate_all_by_template(
    "button_template.png", 
    confidence=0.8, 
    max_results=5
)

# 批量点击
result = wechat_auto.find_and_click_all_buttons(
    "button_template.png", 
    confidence=0.8, 
    max_results=10,
    click_interval=0.5
)
"""
import os
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.locator import CompositeLocator
from core.mouse import MouseController
from core.keyboard import KeyboardController
from core.wechat_detector import WechatProcessDetector, ProcessInfo
from core.utils import logger, config, RpaException
from workflows.wechat.wechat_operations import WechatOperationInterface, OperationResult
from workflows.wechat.exceptions import WechatNotFoundError, WechatWindowError, WechatOperationError


class WechatHalfAuto:
    """企业微信半自动化主控制器"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        初始化主控制器
        
        Args:
            config_override: 配置覆盖项
        """
        self.logger = logger  # 使用全局配置的RpaLogger实例
        
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
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            template_dir = project_root / self.config['templates']['template_dir']
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
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            template_dir = project_root / self.config['templates']['template_dir']
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
            wechat_auto.logger.error("❌ 系统初始化失败")
            return
        
        wechat_auto.logger.info("✅ 系统初始化成功")
        
        # 获取窗口信息
        window_info = wechat_auto.get_wechat_window_info()
        if window_info:
            wechat_auto.logger.info(f"📱 企业微信窗口: {window_info['title']}")
            wechat_auto.logger.info(f"📏 窗口大小: {window_info['width']}x{window_info['height']}")
        
        # 演示截图功能
        wechat_auto.logger.info("\n📸 正在截取操作截图...")
        screenshot_result = wechat_auto.take_screenshot()
        if screenshot_result.success and screenshot_result.data:
            wechat_auto.logger.info(f"✅ 截图成功: {screenshot_result.data['screenshot_path']}")
        else:
            wechat_auto.logger.error(f"❌ 截图失败: {screenshot_result.message}")
    
        # 演示发送消息功能
        wechat_auto.logger.info("\n💬 演示发送消息功能...")
        test_message = "这是一条测试消息"
        
        # 注意：这里需要实际的模板文件才能工作
        # test_templates = ['chat1.png', 'chat2.png']
        # result = wechat_auto.execute_multi_chat_send(test_message, test_templates)
        # print(f"发送结果: {result.message}")
        
        wechat_auto.logger.info("💡 提示：要使用完整功能，请准备聊天模板图片并放置在 templates/wechat/ 目录下")
        
    except Exception as e:
        wechat_auto.logger.error(f"❌ 运行时错误: {str(e)}")
        
    finally:
        # 清理资源
        wechat_auto.cleanup()
        wechat_auto.logger.info("\n🔧 系统清理完成")

def main1():
    """半自动群发点击功能流程"""

    print("半自动群发点击功能流程")
    print("=" * 50)

    # 创建主控制器实例
    wechat_auto = WechatHalfAuto()
    
    try:
        # 初始化系统
        if not wechat_auto.initialize():
            wechat_auto.logger.error("❌ 系统初始化失败")
            return
        
        wechat_auto.logger.info("✅ 系统初始化成功")
        
        # 获取窗口信息
        window_info = wechat_auto.get_wechat_window_info()
        if window_info:
            wechat_auto.logger.info(f"📱 企业微信窗口: {window_info['title']}")
            wechat_auto.logger.info(f"📏 窗口大小: {window_info['width']}x{window_info['height']}")
            wechat_auto.logger.info(f"📏 窗口rect: {window_info['rect']}")
        
        # time.sleep(3)

        # 查找群发按钮
        wechat_auto.logger.info("🔍 正在查找未选框...")
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "templates/wechat/group_button.png"
        locate_result = wechat_auto.get_locator().image_locator.locate_all_by_template(str(template_path), confidence=0.9)
        # 计算所有按钮的中心点坐标
        button_centers = []
        for r in locate_result:
            left, top, right, bottom = r
            center_x = left + (right - left) // 2
            center_y = top + (bottom - top) // 2
            button_centers.append((center_x, center_y))
        
        # 按y轴坐标从低到高排序（从上到下）
        button_centers.sort(key=lambda point: point[1])
        wechat_auto.logger.info(f"🎯 找到 {len(button_centers)} 个群发按钮，按从上到下顺序排列")

        if len(button_centers) < 9:
            wechat_auto.logger.error(f"❌ 找到的群发按钮数量不足，只有 {len(button_centers)} 个，无法进行群发")
            return

        for center_x, center_y in button_centers[:9]:
            wechat_auto.get_mouse_controller().click(center_x, center_y)
            # time.sleep(0.5)

        # 选完后，进行滚轮下滑，开始卡bug
        wechat_auto.logger.info("🖱️ 开始滚轮下滑操作...")
        
        # 方法1：使用高级平滑滚动（推荐）
        try:
            mouse_controller = wechat_auto.get_mouse_controller()
            # 平滑滚动 600 像素，分 20 步完成
            mouse_controller.scroll_smooth(-20, steps=3, delay=0.05)
            wechat_auto.logger.info("✅ 高级平滑滚动完成")
        except Exception as e:
            wechat_auto.logger.warning(f"高级滚动失败，使用备用方案: {e}")
            
            # 方法2：使用多次小幅度滚动（备用方案）
            for i in range(15):
                wechat_auto.get_mouse_controller().scroll(-3)  # 每次滚动3个单位
                time.sleep(0.08)  # 短暂间隔
            wechat_auto.logger.info("✅ 标准滚动完成")
        
        time.sleep(1)

        # 再选3个未选框出来
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "templates/wechat/group_button.png"
        locate_result1 = wechat_auto.get_locator().image_locator.locate_all_by_template(str(template_path), confidence=0.9)
        if len(locate_result1) < 3:
            wechat_auto.logger.error(f"❌ 找到的未选框数量不足，只有 {len(locate_result1)} 个，无法进行群发")
            return
        
        button_centers1 = []
        for r in locate_result1:
            left, top, right, bottom = r
            center_x = left + (right - left) // 2
            center_y = top + (bottom - top) // 2
            button_centers1.append((center_x, center_y))
        button_centers1.sort(key=lambda point: point[1])
        wechat_auto.logger.info(f"🎯 找到 {len(button_centers1)} 个未选框，按从上到下顺序排列")
        # 先按左键，再按右键，再抬右键，再抬左键
        for center_x, center_y in button_centers1[:3]:
            # 移动到目标位置
            wechat_auto.get_mouse_controller().move_to(center_x, center_y, duration=0.1)
            # 执行特殊的鼠标操作序列
            mouse_controller = wechat_auto.get_mouse_controller()
            # 1. 先按左键（不释放）
            mouse_controller.mouse_down(button='left')
            time.sleep(0.05)  # 短暂延迟
            # 2. 再按右键（不释放）
            mouse_controller.mouse_down(button='right')
            time.sleep(0.05)  # 短暂延迟
            # 3. 再抬右键
            mouse_controller.mouse_up(button='right')
            time.sleep(0.05)  # 短暂延迟
            # 4. 再抬左键
            mouse_controller.mouse_up(button='left')
            # 操作间隔
            time.sleep(0.2)

        for center_x, center_y in button_centers1[:3]:
            wechat_auto.get_mouse_controller().click(center_x, center_y)
        for center_x, center_y in button_centers1[:3]:
            wechat_auto.get_mouse_controller().click(center_x, center_y)
            wechat_auto.get_mouse_controller().click(center_x, center_y)
        for center_x, center_y in button_centers1[3:]:
            wechat_auto.get_mouse_controller().click(center_x, center_y)

        wechat_auto.get_mouse_controller().scroll_smooth(-2, steps=1, delay=0.05)

        # 疯狂连点坐标
        # 疯狂连点坐标 - Crazy click coordinates
        window_info = wechat_auto.get_wechat_window_info()
        if window_info and 'rect' in window_info:
            crazy_click_coordinate = (button_centers1[0][0] + 50, window_info['rect'][3] - 10)
            wechat_auto.logger.info(f"🎯 疯狂连点坐标: {crazy_click_coordinate}")
        else:
            wechat_auto.logger.error("❌ 无法获取窗口信息，跳过疯狂连点操作")
            return
        
        time.sleep(1)

        wechat_auto.logger.info("🎯 开始疯狂连点坐标操作")
        # for i in range(100):
        wechat_auto.get_mouse_controller().click(crazy_click_coordinate[0], crazy_click_coordinate[1], clicks=600, interval=0.01)
            # time.sleep(0.1)  # 短暂间隔
        wechat_auto.logger.info("✅ 疯狂连点坐标完成")
        
    except Exception as e:
        wechat_auto.logger.error(f"❌ 运行时错误: {str(e)}")
        
    finally:
        # 清理资源
        wechat_auto.cleanup()
        wechat_auto.logger.info("\n🔧 系统清理完成")

if __name__ == "__main__":
    main1()