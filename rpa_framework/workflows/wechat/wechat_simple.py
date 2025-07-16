"""
企业微信简化工作流
移除过度封装，提供简洁直接的业务逻辑接口

重构改进：
1. 移除 WechatOperationInterface 过度封装
2. 直接使用 core 模块的功能
3. 简化返回值，使用异常处理而非结果包装
4. 清晰的业务流程方法
"""

import sys
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.workflow_base import WorkflowBase
from core.mouse_helpers import (
    crazy_click, find_template_centers,
    TemplateNotFound
)
from core.wechat_detector import WechatProcessDetector
from config.settings import get_config, get_settings
from workflows.wechat.exceptions import WechatNotFoundError, WechatWindowError, WechatOperationError


class WechatWorkflow(WorkflowBase):
    """企业微信工作流 - 简化版"""
    
    def __init__(self, debug_mode: bool = False):
        super().__init__("WechatWorkflow", debug_mode)
        
        # 企业微信相关组件
        self.process_detector = WechatProcessDetector()
        self.current_process = None
        self.current_window = None
        
        # 配置
        self.wechat_config = self.settings.wechat
        
    def run(self) -> bool:
        """默认运行流程：初始化和窗口调整"""
        return self.initialize_and_adjust_window()
    
    def initialize_and_adjust_window(self) -> bool:
        """
        初始化系统并调整窗口
        
        Returns:
            是否成功
            
        Raises:
            WechatNotFoundError: 企业微信未找到
            WechatWindowError: 窗口操作失败
        """
        try:
            # 检测企业微信进程
            processes = self.process_detector.find_wechat_processes()
            if not processes:
                raise WechatNotFoundError("未找到企业微信进程")
            
            self.current_process = processes[0]
            self._log_operation(f"找到企业微信进程: {self.current_process.name} (PID: {self.current_process.pid})")
            
            # 查找并激活窗口
            hwnd = self.locator.window_locator.find_window_by_title("企业微信")
            if not hwnd:
                raise WechatWindowError("未找到企业微信窗口")
            
            self.current_window = hwnd
            
            # 激活窗口
            if not self.locator.window_locator.activate_window(hwnd):
                raise WechatWindowError("激活企业微信窗口失败")
            
            self._log_operation("企业微信窗口已激活")
            
            # 调整窗口大小和位置
            window_config = self.wechat_config.window_size
            position_config = self.wechat_config.window_position
            
            success = self.locator.window_locator.set_window_size_and_position(
                hwnd,
                position_config["x"],
                position_config["y"],
                window_config["width"],
                window_config["height"]
            )
            
            if success:
                self._log_operation(f"窗口调整成功: {window_config['width']}x{window_config['height']} at ({position_config['x']}, {position_config['y']})")
            else:
                self.logger.warning("窗口调整失败，继续执行")
            
            # 等待窗口稳定
            self.sleep(1.0, "等待窗口调整完成")
            
            return True
            
        except (WechatNotFoundError, WechatWindowError):
            raise
        except Exception as e:
            raise WechatOperationError(f"初始化失败: {e}")
    
    def find_and_click_wechat_element(self, template_name: str, 
                                     confidence: Optional[float] = None,
                                     timeout: float = 5.0,
                                     required: bool = True) -> bool:
        """
        查找并点击企业微信界面元素
        
        Args:
            template_name: 模板名称
            confidence: 置信度
            timeout: 超时时间
            required: 是否必需找到
            
        Returns:
            是否成功点击
            
        Raises:
            WechatOperationError: 操作失败（当required=True时）
        """
        if confidence is None:
            confidence = self.wechat_config.template_confidence
        
        try:
            result = self.find_and_click(template_name, confidence, timeout)
            
            if not result and required:
                raise WechatOperationError(f"必需的元素未找到: {template_name}")
            
            return result
            
        except TemplateNotFound as e:
            if required:
                raise WechatOperationError(f"必需的元素未找到: {template_name}")
            return False
    
    def find_all_and_click_wechat_elements(self, template_name: str,
                                         confidence: Optional[float] = None,
                                         max_count: int = 10) -> int:
        """
        查找并点击所有匹配的企业微信元素
        
        Args:
            template_name: 模板名称
            confidence: 置信度
            max_count: 最大点击数量
            
        Returns:
            实际点击数量
        """
        if confidence is None:
            confidence = self.wechat_config.template_confidence
        
        return self.find_all_and_click(template_name, confidence, max_count)
    
    def setup_multiselect_mode(self) -> bool:
        """
        设置多选模式
        
        Returns:
            是否成功
            
        Raises:
            WechatOperationError: 操作失败
        """
        try:
            self._log_operation("开始设置多选模式")
            
            # 查找并点击多选按钮
            if not self.find_and_click_wechat_element("multiselect_button.png"):
                raise WechatOperationError("未找到多选按钮")
            
            # 等待多选模式激活
            self.sleep(0.5, "等待多选模式激活")
            
            self._log_operation("多选模式设置成功")
            return True
            
        except Exception as e:
            raise WechatOperationError(f"设置多选模式失败: {e}")
    
    def select_groups(self, group_template: str, 
                     max_groups: int = 50,
                     confidence: Optional[float] = None) -> int:
        """
        选择群组
        
        Args:
            group_template: 群组模板
            max_groups: 最大选择数量
            confidence: 置信度
            
        Returns:
            实际选择的群组数量
        """
        if confidence is None:
            confidence = self.wechat_config.template_confidence
        
        try:
            self._log_operation(f"开始选择群组: {group_template}")
            
            # 查找所有群组并点击
            count = self.find_all_and_click_wechat_elements(
                group_template, confidence, max_groups
            )
            
            if count == 0:
                raise WechatOperationError(f"未找到群组: {group_template}")
            
            self._log_operation(f"成功选择 {count} 个群组")
            return count
            
        except Exception as e:
            raise WechatOperationError(f"选择群组失败: {e}")
    
    def send_message(self, message_template: str = "send_button.png") -> bool:
        """
        发送消息
        
        Args:
            message_template: 发送按钮模板
            
        Returns:
            是否成功
            
        Raises:
            WechatOperationError: 发送失败
        """
        try:
            self._log_operation("开始发送消息")
            
            # 点击发送按钮
            if not self.find_and_click_wechat_element(message_template):
                raise WechatOperationError("未找到发送按钮")
            
            # 等待发送完成
            send_delay = self.wechat_config.message_send_delay
            self.sleep(send_delay, "等待消息发送")
            
            self._log_operation("消息发送成功")
            return True
            
        except Exception as e:
            raise WechatOperationError(f"发送消息失败: {e}")
    
    def perform_crazy_click(self, template_name: str,
                           groups: Optional[int] = None,
                           clicks_per_group: Optional[int] = None) -> bool:
        """
        执行疯狂点击
        
        Args:
            template_name: 目标模板
            groups: 分组数量
            clicks_per_group: 每组点击次数
            
        Returns:
            是否成功
            
        Raises:
            WechatOperationError: 操作失败
        """
        try:
            # 获取配置
            crazy_config = self.wechat_config.crazy_click_settings
            final_groups = groups or crazy_config["total_groups"]
            final_clicks_per_group = clicks_per_group or crazy_config["clicks_per_group"]
            
            self._log_operation(f"开始疯狂点击: {template_name}, {final_groups}组x{final_clicks_per_group}次")
            
            # 查找目标位置
            centers = find_template_centers(template_name, 
                                          self.wechat_config.template_confidence,
                                          max_results=1)
            
            if not centers:
                raise WechatOperationError(f"未找到疯狂点击目标: {template_name}")
            
            target_x, target_y = centers[0]
            
            # 执行疯狂点击
            crazy_click(target_x, target_y, final_groups, final_clicks_per_group,
                       group_delay=crazy_config["group_interval"],
                       click_delay=crazy_config["click_interval"])
            
            self._log_operation("疯狂点击完成")
            return True
            
        except TemplateNotFound as e:
            raise WechatOperationError(f"疯狂点击目标未找到: {template_name}")
        except Exception as e:
            raise WechatOperationError(f"疯狂点击失败: {e}")
    
    def scroll_contact_list(self, direction: str = "down", 
                           amount: int = 500,
                           steps: int = 3) -> None:
        """
        滚动联系人列表
        
        Args:
            direction: 滚动方向
            amount: 滚动量
            steps: 分步数
        """
        try:
            self._log_operation(f"滚动联系人列表: {direction} {amount}像素")
            
            # 获取窗口信息来确定滚动区域
            if self.current_window:
                window_info = self.locator.window_locator.get_window_info(self.current_window)
                if window_info:
                    # 在窗口中心左侧区域滚动（通常是联系人列表区域）
                    scroll_x = window_info.rect[0] + window_info.width // 4
                    scroll_y = window_info.center[1]
                    
                    self.scroll_area(direction, amount, scroll_x, scroll_y)
                    return
            
            # 如果无法获取窗口信息，使用默认滚动
            self.scroll_area(direction, amount)
            
        except Exception as e:
            self.logger.warning(f"滚动联系人列表失败: {e}")
    
    def wait_for_wechat_element(self, template_names: List[str],
                               timeout: float = 10.0,
                               confidence: Optional[float] = None) -> Optional[str]:
        """
        等待企业微信元素出现
        
        Args:
            template_names: 模板名称列表
            timeout: 超时时间
            confidence: 置信度
            
        Returns:
            找到的模板名称或None
        """
        if confidence is None:
            confidence = self.wechat_config.template_confidence
        
        return self.wait_for_templates(template_names, timeout, confidence)
    
    def execute_mass_sending_workflow(self, group_template: str,
                                    max_groups: int = 50,
                                    use_crazy_click: bool = False) -> bool:
        """
        执行群发工作流
        
        Args:
            group_template: 群组模板
            max_groups: 最大群组数
            use_crazy_click: 是否使用疯狂点击
            
        Returns:
            是否成功
            
        Raises:
            WechatOperationError: 工作流执行失败
        """
        try:
            self._log_operation("开始执行群发工作流")
            
            # 1. 初始化和窗口调整
            if not self.initialize_and_adjust_window():
                raise WechatOperationError("初始化失败")
            
            # 2. 设置多选模式
            if not self.setup_multiselect_mode():
                raise WechatOperationError("设置多选模式失败")
            
            # 3. 选择群组
            selected_count = self.select_groups(group_template, max_groups)
            if selected_count == 0:
                raise WechatOperationError("未选择到任何群组")
            
            # 4. 发送消息
            if use_crazy_click:
                # 使用疯狂点击发送
                if not self.perform_crazy_click("send_button.png"):
                    raise WechatOperationError("疯狂点击发送失败")
            else:
                # 普通发送
                if not self.send_message():
                    raise WechatOperationError("发送消息失败")
            
            self._log_operation(f"群发工作流执行成功，发送到 {selected_count} 个群组")
            return True
            
        except Exception as e:
            self.error_count += 1
            raise WechatOperationError(f"群发工作流执行失败: {e}")
    
    def perform_semi_auto_mass_sending_original(self) -> bool:
        """
        执行原版半自动群发操作的核心逻辑 - 保持所有RPA细节
        
        这是从原 wechat_half_auto.py 中的 perform_semi_auto_mass_sending() 移植的完整逻辑
        
        Returns:
            bool: 是否成功
        """
        try:
            # 更新窗口信息并保存配置
            self._log_operation("🔄 正在更新窗口信息...")
            if self.current_window:
                try:
                    # 获取最新的窗口信息
                    updated_window_info = self.locator.window_locator.get_window_info(self.current_window)
                    
                    if updated_window_info:
                        self._log_operation(f"📏 当前窗口信息: 大小({updated_window_info.width}x{updated_window_info.height}), "
                                         f"位置({updated_window_info.rect[0]}, {updated_window_info.rect[1]})")
                        
                        # 保存到settings.yaml (使用全局配置管理器)
                        from config.settings import get_settings
                        settings = get_settings()
                        success = settings.update_wechat_window_config(
                            width=updated_window_info.width, 
                            height=updated_window_info.height, 
                            x=updated_window_info.rect[0],  # left
                            y=updated_window_info.rect[1]   # top
                        )
                        
                        if success:
                            self._log_operation("💾 窗口配置已自动保存，下次启动时将使用新配置")
                        else:
                            self.logger.warning("⚠️ 窗口配置保存失败，但不影响当前操作")
                            
                    else:
                        self.logger.warning("⚠️ 无法获取最新窗口信息，使用缓存信息")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ 更新窗口信息时出错，继续使用缓存信息: {str(e)}")

            # 执行半自动群发流程
            self._log_operation("🔍 开始半自动群发流程...")
            
            # 1. 查找并点击前9个群发按钮
            self._log_operation("🔍 正在查找未选框...")
            button_centers = self._find_template_centers_with_sort("group_button.png", confidence=0.9)
            
            self._log_operation(f"🎯 找到 {len(button_centers)} 个群发按钮，按从上到下顺序排列")

            if len(button_centers) < 9:
                self.logger.error(f"❌ 找到的群发按钮数量不足，只有 {len(button_centers)} 个，无法进行群发")
                return False

            # 点击前9个按钮 (跳过第一个，从第二个开始，共点击1-9位置的按钮)
            self._click_buttons_with_delay(button_centers[1:10], delay=0)

            # 2. 进行滚轮下滑操作
            self._perform_scroll_operation("major")
            
            self.sleep(1.0, "等待滚动完成")

            # 3. 再选3个未选框并执行特殊点击序列
            self._log_operation("🔍 查找滚动后的未选框...")
            button_centers1 = self._find_template_centers_with_sort("group_button.png", confidence=0.9)
            
            if len(button_centers1) < 3:
                self.logger.error(f"❌ 找到的未选框数量不足，只有 {len(button_centers1)} 个，无法进行群发")
                return False
            
            self._log_operation(f"🎯 找到 {len(button_centers1)} 个未选框，按从上到下顺序排列")
            
            # 执行特殊点击序列（左键+右键组合）
            self._perform_special_click_sequence(button_centers1, count=3)

            # 多次点击前3个按钮
            self._click_buttons_with_delay(button_centers1[:3], delay=0)
            for center_x, center_y in button_centers1[:3]:
                self.mouse.click(center_x, center_y)
                self.mouse.click(center_x, center_y)
            
            # 点击剩余按钮
            self._click_buttons_with_delay(button_centers1[3:], delay=0)

            # 轻微滚动
            self._perform_scroll_operation("minor")

            # 4. 疯狂连点操作
            window_info = self.locator.window_locator.get_window_info(self.current_window)
            if window_info:
                crazy_click_coordinate = (button_centers1[0][0] + 50, window_info.rect[3] - 10)
                self._log_operation(f"🎯 疯狂连点坐标: {crazy_click_coordinate}")
                self.sleep(1.0, "准备疯狂连点")
                # 使用多组连点方法
                if not self._perform_multi_group_crazy_click(crazy_click_coordinate[0], crazy_click_coordinate[1]):
                    return False
            else:
                self.logger.error("❌ 无法获取窗口信息，跳过疯狂连点操作")
                return False
            
            # 5. 最后检查一遍多选框是否全部选中，因为连点不一定会保证选中最后一次
            self._log_operation("🔍 最后检查一遍多选框是否全部选中")
            button_centers = self._find_template_centers_with_sort("group_button.png", confidence=0.9)
            for center_x, center_y in button_centers:
                self.mouse.click(center_x, center_y)

            self._log_operation("✅ 半自动群发点击功能流程执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 半自动群发流程执行失败: {str(e)}")
            return False

    def execute_semi_auto_workflow(self, pause_points: Optional[List[str]] = None) -> bool:
        """
        执行半自动工作流（在关键点暂停等待用户确认）
        
        Args:
            pause_points: 暂停点列表
            
        Returns:
            是否成功
        """
        pause_points = pause_points or ["after_multiselect", "before_send"]
        
        try:
            self._log_operation("开始执行半自动工作流")
            
            # 1. 初始化
            if not self.initialize_and_adjust_window():
                raise WechatOperationError("初始化失败")
            
            # 2. 设置多选模式
            if not self.setup_multiselect_mode():
                raise WechatOperationError("设置多选模式失败")
            
            # 暂停点1：多选模式设置后
            if "after_multiselect" in pause_points:
                input("多选模式已设置，请手动选择群组，然后按回车继续...")
            
            # 暂停点2：发送前
            if "before_send" in pause_points:
                input("请确认选择无误，按回车开始发送...")
            
            # 3. 发送消息
            if not self.send_message():
                raise WechatOperationError("发送消息失败")
            
            self._log_operation("半自动工作流执行成功")
            return True
            
        except Exception as e:
            self.error_count += 1
            raise WechatOperationError(f"半自动工作流执行失败: {e}")
    
    # === 原版RPA逻辑的辅助方法 ===
    
    def _find_template_centers_with_sort(self, template_name: str, confidence: float = 0.8, 
                                       sort_by_y: bool = True, reverse: bool = False) -> List[tuple]:
        """
        查找模板并返回中心点坐标列表，按Y轴排序
        
        Args:
            template_name: 模板文件名
            confidence: 置信度
            sort_by_y: 是否按Y轴排序
            reverse: 排序是否倒序
            
        Returns:
            中心点坐标列表
        """
        try:
            # 查找所有匹配的模板
            template_path = self.get_template_path(template_name)
            locate_result = self.locator.image_locator.locate_all_by_template(str(template_path), confidence=confidence)
            
            if not locate_result:
                return []
            
            # 计算中心点
            button_centers = []
            for r in locate_result:
                left, top, right, bottom, conf = r
                center_x = left + (right - left) // 2
                center_y = top + (bottom - top) // 2
                button_centers.append((center_x, center_y))
            
            # 排序
            if sort_by_y:
                button_centers.sort(key=lambda point: point[1], reverse=reverse)
            
            return button_centers
            
        except Exception as e:
            self.logger.error(f"查找模板中心点失败: {e}")
            return []
    
    def _click_buttons_with_delay(self, button_centers: List[tuple], delay: float = 0.5):
        """
        批量点击按钮并添加延迟
        
        Args:
            button_centers: 按钮中心点坐标列表
            delay: 点击间隔时间
        """
        for center_x, center_y in button_centers:
            self.mouse.click(center_x, center_y)
            if delay > 0:
                self.sleep(delay, f"点击延迟")
    
    def _perform_special_click_sequence(self, button_centers: List[tuple], count: int = 3):
        """
        执行特殊的点击序列（先按左键，再按右键，再抬右键，再抬左键）
        
        Args:
            button_centers: 按钮中心点坐标列表
            count: 执行的按钮数量
        """
        for center_x, center_y in button_centers[:count]:
            # 移动到目标位置
            self.mouse.move_to(center_x, center_y, duration=0.1)
            # 执行特殊的鼠标操作序列
            # 1. 先按左键（不释放）
            self.mouse.mouse_down(button='left')
            self.sleep(0.05, "左键按下")
            # 2. 再按右键（不释放）
            self.mouse.mouse_down(button='right')
            self.sleep(0.05, "右键按下")
            # 3. 再抬右键
            self.mouse.mouse_up(button='right')
            self.sleep(0.05, "右键抬起")
            # 4. 再抬左键
            self.mouse.mouse_up(button='left')
            # 操作间隔
            self.sleep(0.2, "特殊序列间隔")
    
    def _perform_scroll_operation(self, scroll_type: str = "major", custom_pixels: Optional[int] = None, 
                                custom_steps: Optional[int] = None, custom_delay: Optional[float] = None):
        """
        执行滚轮操作的统一方法
        
        Args:
            scroll_type: 滚动类型
                - "major": 主要滚动 (-20像素，3步，0.05秒延迟)
                - "minor": 轻微滚动 (-2像素，1步，0.05秒延迟)  
                - "custom": 自定义滚动
            custom_pixels: 自定义滚动像素数（仅在scroll_type="custom"时生效）
            custom_steps: 自定义滚动步数（仅在scroll_type="custom"时生效）
            custom_delay: 自定义延迟时间（仅在scroll_type="custom"时生效）
        """
        try:
            # 根据滚动类型设置参数
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
                
            self._log_operation(f"🖱️ 开始{scroll_name}操作...")
            
            # 方法1：尝试高级平滑滚动
            try:
                self.mouse.scroll_smooth(pixels, steps=steps, delay=delay)
                self._log_operation(f"✅ {scroll_name}(高级平滑)完成")
                return True
            except Exception as e:
                self.logger.warning(f"高级滚动失败，使用备用方案: {e}")
                
                # 方法2：备用方案 - 使用多次小幅度滚动
                fallback_clicks = pixels // -3  # 每次滚动3个单位
                if fallback_clicks <= 0:
                    fallback_clicks = 1
                    
                for i in range(fallback_clicks):
                    self.mouse.scroll(-3)
                    self.sleep(0.08, "滚动间隔")
                self._log_operation(f"✅ {scroll_name}(标准滚动)完成")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 滚轮操作失败: {str(e)}")
            return False
    
    def _perform_multi_group_crazy_click(self, x: int, y: int) -> bool:
        """
        执行多组疯狂连点操作
        
        Args:
            x: 点击X坐标
            y: 点击Y坐标
            
        Returns:
            是否成功
        """
        try:
            # 从全局配置中获取疯狂连点配置
            from config.settings import get_settings
            settings = get_settings()
            
            # 验证配置有效性
            if not settings.validate_crazy_click_settings():
                self.logger.error("❌ 疯狂连点配置无效，使用默认参数")
                # 使用默认配置
                click_config = {
                    "clicks_per_group": 100,
                    "group_interval": 2.0,
                    "total_groups": 6,
                    "click_interval": 0.01
                }
            else:
                click_config = settings.get_crazy_click_config()
            
            self._log_operation(f"🎯 开始多组疯狂连点操作:")
            self._log_operation(f"   📊 配置参数: {click_config['total_groups']}组, 每组{click_config['clicks_per_group']}次, 组间隔{click_config['group_interval']}s")
            self._log_operation(f"   🎯 点击坐标: ({x}, {y})")
            
            # 执行多组连点
            for group_num in range(click_config['total_groups']):
                self._log_operation(f"🎯 执行第 {group_num + 1}/{click_config['total_groups']} 组连点...")
                
                # 执行一组连点
                self.mouse.click(
                    x, y, 
                    clicks=click_config['clicks_per_group'],
                    interval=click_config['click_interval']
                )
                
                self._log_operation(f"✅ 第 {group_num + 1} 组连点完成 ({click_config['clicks_per_group']}次)")
                
                # 组间间隔（最后一组不需要等待）
                if group_num < click_config['total_groups'] - 1:
                    self._log_operation(f"⏱️ 组间间隔等待 {click_config['group_interval']}s...")
                    self.sleep(click_config['group_interval'], "组间间隔")
            
            self._log_operation(f"✅ 多组疯狂连点操作完成 (总计: {click_config['total_groups'] * click_config['clicks_per_group']}次)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 多组疯狂连点操作失败: {str(e)}")
            return False


# 便捷函数
def create_wechat_workflow(debug_mode: bool = False) -> WechatWorkflow:
    """创建企业微信工作流实例"""
    return WechatWorkflow(debug_mode)


def quick_mass_send(group_template: str, 
                   max_groups: int = 50,
                   use_crazy_click: bool = False,
                   debug_mode: bool = False) -> bool:
    """
    快速群发函数
    
    Args:
        group_template: 群组模板
        max_groups: 最大群组数
        use_crazy_click: 是否使用疯狂点击
        debug_mode: 是否启用调试模式
        
    Returns:
        是否成功
    """
    workflow = WechatWorkflow(debug_mode)
    return workflow.execute_mass_sending_workflow(group_template, max_groups, use_crazy_click)


def quick_semi_auto_send(debug_mode: bool = False) -> bool:
    """
    快速半自动发送
    
    Args:
        debug_mode: 是否启用调试模式
        
    Returns:
        是否成功
    """
    workflow = WechatWorkflow(debug_mode)
    return workflow.execute_semi_auto_workflow()


def quick_semi_auto_send_original(debug_mode: bool = False) -> bool:
    """
    快速半自动发送 - 使用原版精确RPA逻辑
    
    这个函数使用从原 wechat_half_auto.py 移植的完整逻辑，
    保持所有精确的点击序列、滚动操作和疯狂连点功能
    
    Args:
        debug_mode: 是否启用调试模式
        
    Returns:
        是否成功
    """
    workflow = WechatWorkflow(debug_mode)
    try:
        # 初始化系统并调整窗口
        if not workflow.initialize_and_adjust_window():
            return False
        
        # 执行原版半自动群发逻辑
        return workflow.perform_semi_auto_mass_sending_original()
        
    except Exception as e:
        workflow.logger.error(f"快速半自动发送失败: {e}")
        return False


def main_semi_auto_original():
    """
    半自动群发点击功能流程 - 原版逻辑
    
    这是对原 wechat_half_auto.py 中 main_semi_auto() 函数的完整重现，
    包含所有用户交互和确认流程
    """
    print("半自动群发点击功能流程 - 原版逻辑")
    print("=" * 50)

    # 创建工作流实例
    workflow = WechatWorkflow(debug_mode=False)
    
    try:
        # 1. 初始化系统并调整窗口
        if not workflow.initialize_and_adjust_window():
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
            workflow.logger.info("❌ 用户取消操作")
            print("操作已取消")
            return
        
        workflow.logger.info("✅ 用户确认继续，开始执行群发操作...")

        # 执行半自动群发流程
        if not workflow.perform_semi_auto_mass_sending_original():
            workflow.logger.error("❌ 半自动群发操作执行失败")
            return
        
    except Exception as e:
        workflow.logger.error(f"❌ 运行时错误: {str(e)}")
        
    finally:
        # 清理资源 (WorkflowBase会自动处理)
        workflow.logger.info("\n🔧 系统清理完成")