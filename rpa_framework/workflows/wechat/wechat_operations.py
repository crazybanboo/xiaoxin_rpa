"""
企业微信操作接口模块
提供封装的图像识别、鼠标操作、键盘操作等接口
"""
import time
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

from ...core.locator import CompositeLocator, ImageLocator
from ...core.mouse import MouseController
from ...core.keyboard import KeyboardController
from ...core.utils import RpaException, screen_capture
from .exceptions import WechatOperationError


@dataclass
class OperationResult:
    """操作结果数据结构"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None


class WechatOperationInterface:
    """企业微信操作接口类"""
    
    def __init__(self, locator: CompositeLocator, mouse: MouseController, 
                 keyboard: KeyboardController, config: Dict[str, Any]):
        """
        初始化操作接口
        
        Args:
            locator: 定位器实例
            mouse: 鼠标控制器实例
            keyboard: 键盘控制器实例
            config: 配置字典
        """
        self.locator = locator
        self.mouse = mouse
        self.keyboard = keyboard
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 从配置中获取参数
        self.operation_delay = config.get('operation_delay', 0.5)
        self.template_confidence = config.get('template_confidence', 0.8)
        self.multi_select_interval = config.get('multi_select_interval', 0.2)
        self.message_send_delay = config.get('message_send_delay', 1.0)
    
    def find_button_by_template(self, template_path: str, confidence: Optional[float] = None) -> OperationResult:
        """
        通过模板图像查找按钮
        
        Args:
            template_path: 模板图像路径
            confidence: 匹配置信度，默认使用配置值
            
        Returns:
            OperationResult: 包含找到的按钮位置信息
        """
        try:
            confidence = confidence or self.template_confidence
            self.logger.debug(f"查找按钮模板: {template_path}, 置信度: {confidence}")
            
            # 获取当前屏幕截图
            screenshot = screen_capture.screenshot()
            
            # 使用图像定位器查找模板
            result = self.locator.image_locator.locate_by_template(template_path, confidence=confidence)
            
            if result:
                left, top, right, bottom = result
                x, y = left + (right - left) // 2, top + (bottom - top) // 2
                self.logger.info(f"成功找到按钮，位置: ({x}, {y})")
                return OperationResult(
                    success=True,
                    message="按钮找到",
                    data={"position": (x, y)}
                )
            else:
                self.logger.warning(f"未找到按钮模板: {template_path}")
                return OperationResult(
                    success=False,
                    message="按钮未找到",
                    error_code="BUTTON_NOT_FOUND"
                )
                
        except Exception as e:
            self.logger.error(f"查找按钮时发生错误: {str(e)}")
            return OperationResult(
                success=False,
                message=f"查找按钮失败: {str(e)}",
                error_code="BUTTON_SEARCH_ERROR"
            )
    
    def find_checkbox_by_template(self, template_path: str, confidence: Optional[float] = None) -> OperationResult:
        """
        通过模板图像查找多选框
        
        Args:
            template_path: 模板图像路径
            confidence: 匹配置信度，默认使用配置值
            
        Returns:
            OperationResult: 包含找到的多选框位置列表
        """
        try:
            confidence = confidence or self.template_confidence
            self.logger.debug(f"查找多选框模板: {template_path}, 置信度: {confidence}")
            
            # 使用图像定位器查找所有匹配的模板
            # 注意：这里简化实现，实际可能需要多次调用locate_by_template
            result = self.locator.image_locator.locate_by_template(template_path, confidence=confidence)
            
            if result:
                left, top, right, bottom = result
                x, y = left + (right - left) // 2, top + (bottom - top) // 2
                positions = [(x, y)]  # 简化实现，只返回一个位置
                self.logger.info(f"成功找到 {len(positions)} 个多选框")
                return OperationResult(
                    success=True,
                    message=f"找到 {len(positions)} 个多选框",
                    data={"positions": positions}
                )
            else:
                self.logger.warning(f"未找到多选框模板: {template_path}")
                return OperationResult(
                    success=False,
                    message="多选框未找到",
                    error_code="CHECKBOX_NOT_FOUND"
                )
                
        except Exception as e:
            self.logger.error(f"查找多选框时发生错误: {str(e)}")
            return OperationResult(
                success=False,
                message=f"查找多选框失败: {str(e)}",
                error_code="CHECKBOX_SEARCH_ERROR"
            )
    
    def click_at_position(self, x: int, y: int, delay: Optional[float] = None) -> OperationResult:
        """
        在指定位置点击
        
        Args:
            x: X坐标
            y: Y坐标
            delay: 点击后延迟时间，默认使用配置值
            
        Returns:
            OperationResult: 点击操作结果
        """
        try:
            delay = delay or self.operation_delay
            self.logger.debug(f"点击位置: ({x}, {y}), 延迟: {delay}s")
            
            # 执行点击操作
            self.mouse.click(x, y)
            
            # 等待延迟
            if delay is not None and delay > 0:
                time.sleep(delay)
            
            self.logger.info(f"成功点击位置: ({x}, {y})")
            return OperationResult(
                success=True,
                message="点击成功",
                data={"position": (x, y)}
            )
            
        except Exception as e:
            self.logger.error(f"点击操作失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"点击失败: {str(e)}",
                error_code="CLICK_ERROR"
            )
    
    def multi_select_click(self, positions: List[Tuple[int, int]], interval: Optional[float] = None) -> OperationResult:
        """
        多选点击操作
        
        Args:
            positions: 要点击的位置列表
            interval: 点击间隔时间，默认使用配置值
            
        Returns:
            OperationResult: 多选点击操作结果
        """
        try:
            interval = interval or self.multi_select_interval
            self.logger.debug(f"执行多选点击，位置数量: {len(positions)}, 间隔: {interval}s")
            
            success_count = 0
            failed_positions = []
            
            for i, (x, y) in enumerate(positions):
                try:
                    # 执行点击
                    self.mouse.click(x, y)
                    success_count += 1
                    self.logger.debug(f"成功点击位置 {i+1}/{len(positions)}: ({x}, {y})")
                    
                    # 等待间隔（最后一个点击不需要等待）
                    if i < len(positions) - 1 and interval is not None and interval > 0:
                        time.sleep(interval)
                        
                except Exception as e:
                    self.logger.warning(f"点击位置 ({x}, {y}) 失败: {str(e)}")
                    failed_positions.append((x, y))
            
            if success_count == len(positions):
                self.logger.info(f"多选点击完全成功，共点击 {success_count} 个位置")
                return OperationResult(
                    success=True,
                    message=f"多选点击成功，共点击 {success_count} 个位置",
                    data={"success_count": success_count, "total_count": len(positions)}
                )
            else:
                self.logger.warning(f"多选点击部分成功，成功: {success_count}, 失败: {len(failed_positions)}")
                return OperationResult(
                    success=False,
                    message=f"多选点击部分失败，成功: {success_count}, 失败: {len(failed_positions)}",
                    data={
                        "success_count": success_count,
                        "total_count": len(positions),
                        "failed_positions": failed_positions
                    },
                    error_code="MULTI_CLICK_PARTIAL_FAILURE"
                )
                
        except Exception as e:
            self.logger.error(f"多选点击操作失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"多选点击失败: {str(e)}",
                error_code="MULTI_CLICK_ERROR"
            )
    
    def type_message(self, message: str, delay: Optional[float] = None) -> OperationResult:
        """
        输入消息文本
        
        Args:
            message: 要输入的消息
            delay: 输入后延迟时间，默认使用配置值
            
        Returns:
            OperationResult: 输入操作结果
        """
        try:
            delay = delay or self.operation_delay
            self.logger.debug(f"输入消息: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # 执行文本输入
            self.keyboard.type_text(message)
            
            # 等待延迟
            if delay is not None and delay > 0:
                time.sleep(delay)
            
            self.logger.info(f"成功输入消息，长度: {len(message)}")
            return OperationResult(
                success=True,
                message="消息输入成功",
                data={"message_length": len(message)}
            )
            
        except Exception as e:
            self.logger.error(f"输入消息失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"输入消息失败: {str(e)}",
                error_code="TYPE_MESSAGE_ERROR"
            )
    
    def send_message(self, delay: Optional[float] = None) -> OperationResult:
        """
        发送消息（按回车键）
        
        Args:
            delay: 发送后延迟时间，默认使用配置值
            
        Returns:
            OperationResult: 发送操作结果
        """
        try:
            delay = delay or self.message_send_delay
            self.logger.debug(f"发送消息，延迟: {delay}s")
            
            # 按回车键发送消息
            self.keyboard.press_key('enter')
            
            # 等待延迟
            if delay is not None and delay > 0:
                time.sleep(delay)
            
            self.logger.info("成功发送消息")
            return OperationResult(
                success=True,
                message="消息发送成功"
            )
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"发送消息失败: {str(e)}",
                error_code="SEND_MESSAGE_ERROR"
            )
    
    def execute_send_to_multiple_chats(self, message: str, chat_templates: List[str]) -> OperationResult:
        """
        执行向多个聊天发送消息的完整流程
        
        Args:
            message: 要发送的消息
            chat_templates: 聊天模板路径列表
            
        Returns:
            OperationResult: 完整操作结果
        """
        try:
            self.logger.info(f"开始向 {len(chat_templates)} 个聊天发送消息")
            
            success_count = 0
            failed_chats = []
            
            for i, template_path in enumerate(chat_templates):
                try:
                    self.logger.debug(f"处理聊天 {i+1}/{len(chat_templates)}: {template_path}")
                    
                    # 1. 查找聊天
                    find_result = self.find_button_by_template(template_path)
                    if not find_result.success:
                        failed_chats.append({"template": template_path, "error": "聊天未找到"})
                        continue
                    
                    # 2. 点击聊天
                    if find_result.data and "position" in find_result.data:
                        chat_pos = find_result.data["position"]
                        click_result = self.click_at_position(chat_pos[0], chat_pos[1])
                        if not click_result.success:
                            failed_chats.append({"template": template_path, "error": "点击聊天失败"})
                            continue
                    else:
                        failed_chats.append({"template": template_path, "error": "无法获取聊天位置"})
                        continue
                    
                    # 3. 输入消息
                    type_result = self.type_message(message)
                    if not type_result.success:
                        failed_chats.append({"template": template_path, "error": "输入消息失败"})
                        continue
                    
                    # 4. 发送消息
                    send_result = self.send_message()
                    if not send_result.success:
                        failed_chats.append({"template": template_path, "error": "发送消息失败"})
                        continue
                    
                    success_count += 1
                    self.logger.info(f"成功向聊天 {i+1} 发送消息")
                    
                except Exception as e:
                    self.logger.warning(f"处理聊天 {template_path} 时发生错误: {str(e)}")
                    failed_chats.append({"template": template_path, "error": str(e)})
            
            if success_count == len(chat_templates):
                self.logger.info(f"所有聊天发送成功，共 {success_count} 个")
                return OperationResult(
                    success=True,
                    message=f"所有聊天发送成功，共 {success_count} 个",
                    data={"success_count": success_count, "total_count": len(chat_templates)}
                )
            else:
                self.logger.warning(f"部分聊天发送失败，成功: {success_count}, 失败: {len(failed_chats)}")
                return OperationResult(
                    success=False,
                    message=f"部分聊天发送失败，成功: {success_count}, 失败: {len(failed_chats)}",
                    data={
                        "success_count": success_count,
                        "total_count": len(chat_templates),
                        "failed_chats": failed_chats
                    },
                    error_code="MULTI_CHAT_PARTIAL_FAILURE"
                )
                
        except Exception as e:
            self.logger.error(f"多聊天发送操作失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"多聊天发送失败: {str(e)}",
                error_code="MULTI_CHAT_SEND_ERROR"
            )
    
    def take_operation_screenshot(self, filename: Optional[str] = None) -> OperationResult:
        """
        截取操作截图
        
        Args:
            filename: 截图文件名，如果为None则自动生成
            
        Returns:
            OperationResult: 截图操作结果
        """
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"wechat_operation_{timestamp}.png"
            
            self.logger.debug(f"截取操作截图: {filename}")
            
            screenshot_path = screen_capture.screenshot(filename=filename)
            
            self.logger.info(f"成功截取操作截图: {screenshot_path}")
            return OperationResult(
                success=True,
                message="截图成功",
                data={"screenshot_path": screenshot_path}
            )
            
        except Exception as e:
            self.logger.error(f"截取截图失败: {str(e)}")
            return OperationResult(
                success=False,
                message=f"截图失败: {str(e)}",
                error_code="SCREENSHOT_ERROR"
            ) 