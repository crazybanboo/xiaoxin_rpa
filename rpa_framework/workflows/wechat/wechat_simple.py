"""
企业微信简化工作流
移除过度封装，提供简洁直接的业务逻辑接口

重构改进：
1. 移除 WechatOperationInterface 过度封装
2. 直接使用 core 模块的功能
3. 简化返回值，使用异常处理而非结果包装
4. 清晰的业务流程方法
"""

from typing import List, Optional

from ...core.workflow_base import WorkflowBase
from ...core.mouse_helpers import (
    crazy_click, find_template_centers,
    TemplateNotFound
)
from ...core.wechat_detector import WechatProcessDetector
from ...config.settings import get_config, get_settings
from .exceptions import WechatNotFoundError, WechatWindowError, WechatOperationError


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