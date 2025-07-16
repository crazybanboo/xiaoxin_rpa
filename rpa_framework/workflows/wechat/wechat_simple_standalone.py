"""
企业微信半自动化 - 独立版本
移植原版逻辑，避免复杂的依赖关系
"""

import sys
import time
import random
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入必要的核心模块
from core.locator import CompositeLocator
from core.mouse import MouseController
from core.keyboard import KeyboardController
from core.wechat_detector import WechatProcessDetector, ProcessInfo
from core.utils import logger, config, RpaException
from config.settings import get_settings
from workflows.wechat.exceptions_minimal import WechatNotFoundError, WechatWindowError, WechatOperationError


class WechatSemiAutoStandalone:
    """企业微信半自动化 - 独立版本"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        初始化半自动化控制器
        
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
        """初始化企业微信半自动化系统"""
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
            
            # 检查窗口是否为有效的主窗口
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
    
    def adjust_wechat_window(self) -> bool:
        """调整企业微信窗口大小和位置"""
        if not self.is_initialized:
            self.logger.error("系统未初始化")
            return False
        
        if not self.current_window_info:
            self.logger.error("无法获取窗口信息")
            return False
        
        try:
            # 从配置中获取窗口设置
            wechat_config = self.config.get('wechat', {})
            window_size = wechat_config.get('window_size', {})
            window_position = wechat_config.get('window_position', {})
            
            target_width = window_size.get('width', 1200)
            target_height = window_size.get('height', 800)
            target_x = window_position.get('x', 100)
            target_y = window_position.get('y', 100)
            
            hwnd = self.current_window_info['hwnd']
            
            # 激活窗口
            if not self.locator.window_locator.activate_window(hwnd):
                self.logger.warning("无法激活企业微信窗口")
            
            # 设置窗口大小和位置
            success = self.locator.window_locator.set_window_size_and_position(
                hwnd, target_x, target_y, target_width, target_height
            )
            
            if success:
                # 更新窗口信息
                time.sleep(0.5)  # 等待窗口调整完成
                new_window_info = self.locator.window_locator.get_window_info(hwnd)
                if new_window_info:
                    self.current_window_info = {
                        'hwnd': new_window_info.hwnd,
                        'title': new_window_info.title,
                        'rect': new_window_info.rect,
                        'width': new_window_info.width,
                        'height': new_window_info.height,
                        'center': new_window_info.center,
                        'is_visible': new_window_info.is_visible
                    }
                
                self.logger.info(f"窗口调整成功: {target_width}x{target_height} at ({target_x}, {target_y})")
                return True
            else:
                self.logger.error("窗口调整失败")
                return False
                
        except Exception as e:
            self.logger.error(f"调整窗口失败: {str(e)}")
            return False
    
    def initialize_system_and_adjust_window(self) -> bool:
        """初始化系统并调整窗口"""
        # 初始化系统
        if not self.initialize():
            self.logger.error("❌ 系统初始化失败")
            return False
        
        self.logger.info("✅ 系统初始化成功")
        
        # 获取并显示窗口信息
        window_info = self.current_window_info
        if window_info:
            self.logger.info(f"📱 企业微信窗口: {window_info['title']}")
            self.logger.info(f"📏 当前窗口大小: {window_info['width']}x{window_info['height']}")
            self.logger.info(f"📏 当前窗口位置: {window_info['rect']}")
        
        # 调整窗口大小和位置
        self.logger.info("🔧 正在调整企业微信窗口大小和位置...")
        adjust_result = self.adjust_wechat_window()
        
        if adjust_result:
            self.logger.info("✅ 窗口调整成功")
            # 获取调整后的窗口信息
            updated_window_info = self.current_window_info
            if updated_window_info:
                self.logger.info(f"📏 调整后窗口大小: {updated_window_info['width']}x{updated_window_info['height']}")
                self.logger.info(f"📏 调整后窗口位置: {updated_window_info['rect']}")
        else:
            self.logger.error("❌ 窗口调整失败")
            # 继续执行，不中断流程
        
        return True
    
    def find_template_and_get_centers(self, template_name: str, confidence: float = 0.8, 
                                     sort_by_y: bool = True, reverse: bool = False) -> List[Tuple[int, int]]:
        """查找模板并返回中心点坐标列表"""
        template_path = project_root / f"templates/wechat/{template_name}"
        locate_result = self.locator.image_locator.locate_all_by_template(str(template_path), confidence=confidence)
        
        if not locate_result:
            return []
        
        button_centers = []
        for r in locate_result:
            left, top, right, bottom, confidence = r
            center_x = left + (right - left) // 2
            center_y = top + (bottom - top) // 2
            button_centers.append((center_x, center_y))
        
        if sort_by_y:
            button_centers.sort(key=lambda point: point[1], reverse=reverse)
        
        return button_centers
    
    def click_buttons_with_delay(self, button_centers: List[Tuple[int, int]], delay: float = 0.5):
        """批量点击按钮并添加延迟"""
        for center_x, center_y in button_centers:
            self.mouse.click(center_x, center_y)
            if delay > 0:
                time.sleep(delay)
    
    def perform_special_click_sequence(self, button_centers: List[Tuple[int, int]], count: int = 3):
        """执行特殊的点击序列"""
        for center_x, center_y in button_centers[:count]:
            # 移动到目标位置
            self.mouse.move_to(center_x, center_y, duration=0.1)
            # 执行特殊的鼠标操作序列
            self.mouse.mouse_down(button='left')
            time.sleep(0.05)
            self.mouse.mouse_down(button='right')
            time.sleep(0.05)
            self.mouse.mouse_up(button='right')
            time.sleep(0.05)
            self.mouse.mouse_up(button='left')
            time.sleep(0.2)
    
    def perform_scroll_operation(self, scroll_type: str = "major", custom_pixels: Optional[int] = None, 
                                custom_steps: Optional[int] = None, custom_delay: Optional[float] = None):
        """执行滚轮操作"""
        try:
            if scroll_type == "major":
                pixels, steps, delay = -20, 3, 0.05
                scroll_name = "主要滚动"
            elif scroll_type == "minor":
                pixels, steps, delay = -2, 1, 0.05
                scroll_name = "轻微滚动"
            elif scroll_type == "custom":
                pixels = custom_pixels if custom_pixels is not None else -10
                steps = custom_steps if custom_steps is not None else 2
                delay = custom_delay if custom_delay is not None else 0.05
                scroll_name = f"自定义滚动({pixels}像素)"
            else:
                self.logger.error(f"❌ 不支持的滚动类型: {scroll_type}")
                return False
                
            self.logger.info(f"🖱️ 开始{scroll_name}操作...")
            
            # 尝试高级平滑滚动
            try:
                self.mouse.scroll_smooth(pixels, steps=steps, delay=delay)
                self.logger.info(f"✅ {scroll_name}(高级平滑)完成")
                return True
            except Exception as e:
                self.logger.warning(f"高级滚动失败，使用备用方案: {e}")
                
                # 备用方案 - 使用多次小幅度滚动
                fallback_clicks = pixels // -3
                if fallback_clicks <= 0:
                    fallback_clicks = 1
                    
                for i in range(fallback_clicks):
                    self.mouse.scroll(-3)
                    time.sleep(0.08)
                self.logger.info(f"✅ {scroll_name}(标准滚动)完成")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 滚轮操作失败: {str(e)}")
            return False
    
    def perform_multi_group_crazy_click(self, x: int, y: int) -> bool:
        """执行多组疯狂连点操作"""
        try:
            # 获取疯狂连点配置
            settings = get_settings()
            
            # 验证配置有效性
            if not settings.validate_crazy_click_settings():
                self.logger.error("❌ 疯狂连点配置无效，使用默认参数")
                click_config = {
                    "clicks_per_group": 100,
                    "group_interval": 2.0,
                    "total_groups": 6,
                    "click_interval": 0.01
                }
            else:
                click_config = settings.get_crazy_click_config()
            
            self.logger.info(f"🎯 开始多组疯狂连点操作:")
            self.logger.info(f"   📊 配置参数: {click_config['total_groups']}组, 每组{click_config['clicks_per_group']}次, 组间隔{click_config['group_interval']}s")
            self.logger.info(f"   🎯 点击坐标: ({x}, {y})")
            
            # 执行多组连点
            for group_num in range(click_config['total_groups']):
                self.logger.info(f"🎯 执行第 {group_num + 1}/{click_config['total_groups']} 组连点...")
                
                # 执行一组连点
                self.mouse.click(
                    x, y, 
                    clicks=click_config['clicks_per_group'],
                    interval=click_config['click_interval']
                )
                
                self.logger.info(f"✅ 第 {group_num + 1} 组连点完成 ({click_config['clicks_per_group']}次)")
                
                # 组间间隔
                if group_num < click_config['total_groups'] - 1:
                    self.logger.info(f"⏱️ 组间间隔等待 {click_config['group_interval']}s...")
                    time.sleep(click_config['group_interval'])
            
            self.logger.info(f"✅ 多组疯狂连点操作完成 (总计: {click_config['total_groups'] * click_config['clicks_per_group']}次)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 多组疯狂连点操作失败: {str(e)}")
            return False
    
    def perform_semi_auto_mass_sending(self) -> bool:
        """执行半自动群发操作的核心逻辑"""
        try:
            # 更新窗口信息并保存配置
            self.logger.info("🔄 正在更新窗口信息...")
            if self.current_window_info:
                try:
                    # 获取最新的窗口信息
                    hwnd = self.current_window_info['hwnd']
                    updated_window_info = self.locator.window_locator.get_window_info(hwnd)
                    
                    if updated_window_info:
                        # 更新内部窗口信息
                        self.current_window_info = {
                            'hwnd': updated_window_info.hwnd,
                            'title': updated_window_info.title,
                            'rect': updated_window_info.rect,
                            'width': updated_window_info.width,
                            'height': updated_window_info.height,
                            'center': updated_window_info.center,
                            'is_visible': updated_window_info.is_visible
                        }
                        
                        self.logger.info(f"📏 当前窗口信息: 大小({updated_window_info.width}x{updated_window_info.height}), "
                                       f"位置({updated_window_info.rect[0]}, {updated_window_info.rect[1]})")
                        
                        # 保存到settings.yaml
                        settings = get_settings()
                        success = settings.update_wechat_window_config(
                            width=updated_window_info.width, 
                            height=updated_window_info.height, 
                            x=updated_window_info.rect[0],
                            y=updated_window_info.rect[1]
                        )
                        
                        if success:
                            self.logger.info("💾 窗口配置已自动保存，下次启动时将使用新配置")
                        else:
                            self.logger.warning("⚠️ 窗口配置保存失败，但不影响当前操作")
                            
                    else:
                        self.logger.warning("⚠️ 无法获取最新窗口信息，使用缓存信息")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ 更新窗口信息时出错，继续使用缓存信息: {str(e)}")

            # 执行半自动群发流程
            self.logger.info("🔍 开始半自动群发流程...")
            
            # 1. 查找并点击前9个群发按钮
            self.logger.info("🔍 正在查找未选框...")
            button_centers = self.find_template_and_get_centers("group_button.png", confidence=0.9)
            
            self.logger.info(f"🎯 找到 {len(button_centers)} 个群发按钮，按从上到下顺序排列")

            if len(button_centers) < 9:
                self.logger.error(f"❌ 找到的群发按钮数量不足，只有 {len(button_centers)} 个，无法进行群发")
                return False

            # 点击前9个按钮 (跳过第一个，从第二个开始)
            self.click_buttons_with_delay(button_centers[1:10], delay=0)

            # 2. 进行滚轮下滑操作
            self.perform_scroll_operation("major")
            
            time.sleep(1)

            # 3. 再选3个未选框并执行特殊点击序列
            self.logger.info("🔍 查找滚动后的未选框...")
            button_centers1 = self.find_template_and_get_centers("group_button.png", confidence=0.9)
            
            if len(button_centers1) < 3:
                self.logger.error(f"❌ 找到的未选框数量不足，只有 {len(button_centers1)} 个，无法进行群发")
                return False
            
            self.logger.info(f"🎯 找到 {len(button_centers1)} 个未选框，按从上到下顺序排列")
            
            # 执行特殊点击序列
            self.perform_special_click_sequence(button_centers1, count=3)

            # 多次点击前3个按钮
            self.click_buttons_with_delay(button_centers1[:3], delay=0)
            for center_x, center_y in button_centers1[:3]:
                self.mouse.click(center_x, center_y)
                self.mouse.click(center_x, center_y)
            
            # 点击剩余按钮
            self.click_buttons_with_delay(button_centers1[3:], delay=0)

            # 轻微滚动
            self.perform_scroll_operation("minor")

            # 4. 疯狂连点操作
            window_info = self.current_window_info
            if window_info and 'rect' in window_info:
                crazy_click_coordinate = (button_centers1[0][0] + 50, window_info['rect'][3] - 10)
                self.logger.info(f"🎯 疯狂连点坐标: {crazy_click_coordinate}")
                time.sleep(1)
                if not self.perform_multi_group_crazy_click(crazy_click_coordinate[0], crazy_click_coordinate[1]):
                    return False
            else:
                self.logger.error("❌ 无法获取窗口信息，跳过疯狂连点操作")
                return False
            
            # 5. 最后检查一遍多选框
            self.logger.info("🔍 最后检查一遍多选框是否全部选中")
            button_centers = self.find_template_and_get_centers("group_button.png", confidence=0.9)
            for center_x, center_y in button_centers:
                self.mouse.click(center_x, center_y)

            self.logger.info("✅ 半自动群发点击功能流程执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 半自动群发流程执行失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理企业微信半自动化系统资源...")
        self.is_initialized = False
        self.current_process = None
        self.current_window_info = None
        self.logger.info("资源清理完成")


def main_semi_auto_original():
    """半自动群发点击功能流程 - 原版逻辑"""
    print("半自动群发点击功能流程 - 原版逻辑")
    print("=" * 50)

    # 创建半自动化控制器实例
    wechat_auto = WechatSemiAutoStandalone()
    
    try:
        # 1. 初始化系统并调整窗口
        if not wechat_auto.initialize_system_and_adjust_window():
            return
        
        # 等待用户确认
        print("\n" + "=" * 60)
        print("🎯 窗口调整完成！")
        print("📋 接下来将执行半自动群发点击功能：")
        print("   1. 查找并点击前9个群发按钮")
        print("   2. 进行滚轮下滑操作")
        print("   3. 再选择3个未选框并执行特殊点击序列")
        print("   4. 进行疯狂连点操作")
        print("\n⚠️  请确保企业微信已准备就绪，并且群发页面已打开")
        print("=" * 60)
        
        # 等待用户确认
        user_input = input("\n🔍 请确认是否继续执行群发操作? (输入 'y' 或 'yes' 继续，其他任意键取消): ").strip().lower()
        
        if user_input not in ['y', 'yes', '是', '确认']:
            wechat_auto.logger.info("❌ 用户取消操作")
            print("操作已取消")
            return
        
        wechat_auto.logger.info("✅ 用户确认继续，开始执行群发操作...")

        # 执行半自动群发流程
        if not wechat_auto.perform_semi_auto_mass_sending():
            wechat_auto.logger.error("❌ 半自动群发操作执行失败")
            return
        
    except Exception as e:
        wechat_auto.logger.error(f"❌ 运行时错误: {str(e)}")
        
    finally:
        # 清理资源
        wechat_auto.cleanup()
        wechat_auto.logger.info("\n🔧 系统清理完成")


if __name__ == "__main__":
    main_semi_auto_original()