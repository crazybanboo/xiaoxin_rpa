"""
RPA框架 - 工作流基础类
提供通用的工作流基础功能和接口

设计目标：
1. 简化工作流编写流程
2. 提供统一的错误处理
3. 集成调试和日志功能
4. 支持配置管理
"""

import time
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .mouse_helpers import (
    find_and_click, find_all_and_click, batch_click, 
    special_click_sequence, crazy_click, smart_scroll,
    wait_and_find_template, find_template_centers,
    TemplateNotFound, MouseOperationError
)
from .vision_debug import debug_template_match, batch_confidence_test
from .locator import CompositeLocator
from .mouse import MouseController
from .keyboard import KeyboardController
from .utils import logger, RpaException
from ..config.settings import get_settings, get_config, with_config_override


class WorkflowBase(ABC):
    """工作流基础类"""
    
    def __init__(self, name: str = None, debug_mode: bool = False):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
            debug_mode: 是否启用调试模式
        """
        self.name = name or self.__class__.__name__
        self.debug_mode = debug_mode or get_config('general.debug_mode', False)
        
        # 初始化组件
        self.settings = get_settings()
        self.locator = CompositeLocator()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # 执行状态
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.error_count = 0
        self.execution_log = []
        
        # 日志器
        self.logger = logger
        
        self.logger.info(f"工作流初始化: {self.name}, 调试模式: {self.debug_mode}")
    
    @abstractmethod
    def run(self) -> bool:
        """
        执行工作流（子类必须实现）
        
        Returns:
            执行是否成功
        """
        pass
    
    def execute(self) -> bool:
        """
        执行工作流（带错误处理和日志）
        
        Returns:
            执行是否成功
        """
        if self.is_running:
            self.logger.warning(f"工作流 {self.name} 正在运行中")
            return False
        
        self.is_running = True
        self.start_time = time.time()
        self.error_count = 0
        
        try:
            self.logger.info(f"开始执行工作流: {self.name}")
            
            # 执行前置检查
            if not self.pre_execute_check():
                self.logger.error("前置检查失败")
                return False
            
            # 执行主逻辑
            result = self.run()
            
            # 执行后置处理
            self.post_execute_cleanup()
            
            if result:
                self.logger.info(f"工作流执行成功: {self.name}")
            else:
                self.logger.error(f"工作流执行失败: {self.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"工作流执行异常: {self.name}, 错误: {e}")
            if self.debug_mode:
                self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return False
        
        finally:
            self.is_running = False
            self.end_time = time.time()
            duration = self.end_time - self.start_time
            self.logger.info(f"工作流执行完成: {self.name}, 耗时: {duration:.2f}秒, 错误数: {self.error_count}")
    
    def pre_execute_check(self) -> bool:
        """前置检查（子类可重写）"""
        return True
    
    def post_execute_cleanup(self):
        """后置清理（子类可重写）"""
        pass
    
    # 便捷的图像操作方法
    def find_and_click(self, template_path: str, 
                       confidence: Optional[float] = None,
                       timeout: float = 5.0,
                       click_offset: Tuple[int, int] = (0, 0)) -> bool:
        """
        查找并点击模板
        
        Args:
            template_path: 模板路径
            confidence: 置信度（None使用配置默认值）
            timeout: 超时时间
            click_offset: 点击偏移
            
        Returns:
            是否成功
        """
        try:
            if confidence is None:
                confidence = get_config('image.confidence', 0.8)
            
            self._log_operation(f"查找并点击: {template_path}, 置信度: {confidence}")
            
            if self.debug_mode:
                debug_template_match(template_path, confidence)
            
            result = find_and_click(template_path, confidence, 
                                  click_offset=click_offset, timeout=timeout)
            
            if result:
                self._log_operation(f"✅ 成功点击: {template_path}")
            else:
                self._log_operation(f"❌ 点击失败: {template_path}")
                self.error_count += 1
            
            return result
            
        except TemplateNotFound as e:
            self._log_operation(f"❌ 模板未找到: {template_path}")
            self.error_count += 1
            if self.debug_mode:
                self.logger.error(f"模板未找到详情: {e}")
            return False
        except Exception as e:
            self._log_operation(f"❌ 点击异常: {template_path}, 错误: {e}")
            self.error_count += 1
            return False
    
    def find_all_and_click(self, template_path: str,
                          confidence: Optional[float] = None,
                          max_clicks: int = 10,
                          click_delay: float = 0.5) -> int:
        """
        查找所有匹配项并批量点击
        
        Args:
            template_path: 模板路径
            confidence: 置信度
            max_clicks: 最大点击数量
            click_delay: 点击延迟
            
        Returns:
            实际点击数量
        """
        try:
            if confidence is None:
                confidence = get_config('image.confidence', 0.8)
            
            self._log_operation(f"批量点击: {template_path}, 最大数量: {max_clicks}")
            
            count = find_all_and_click(template_path, confidence, 
                                     click_delay=click_delay, max_clicks=max_clicks)
            
            self._log_operation(f"✅ 批量点击完成: {template_path}, 点击数量: {count}")
            return count
            
        except TemplateNotFound:
            self._log_operation(f"❌ 模板未找到: {template_path}")
            self.error_count += 1
            return 0
        except Exception as e:
            self._log_operation(f"❌ 批量点击异常: {template_path}, 错误: {e}")
            self.error_count += 1
            return 0
    
    def wait_for_templates(self, template_paths: List[str],
                          timeout: float = 10.0,
                          confidence: Optional[float] = None) -> Optional[str]:
        """
        等待多个模板中的任意一个出现
        
        Args:
            template_paths: 模板路径列表
            timeout: 超时时间
            confidence: 置信度
            
        Returns:
            找到的模板路径或None
        """
        try:
            if confidence is None:
                confidence = get_config('image.confidence', 0.8)
            
            self._log_operation(f"等待模板: {template_paths}, 超时: {timeout}秒")
            
            result = wait_and_find_template(template_paths, confidence, timeout)
            
            if result:
                found_template, region = result
                self._log_operation(f"✅ 找到模板: {found_template}")
                return found_template
            else:
                self._log_operation(f"❌ 超时未找到任何模板")
                self.error_count += 1
                return None
                
        except Exception as e:
            self._log_operation(f"❌ 等待模板异常: {e}")
            self.error_count += 1
            return None
    
    def click_positions(self, positions: List[Tuple[int, int]], 
                       delay: float = 0.5,
                       randomize: bool = True) -> int:
        """
        批量点击指定位置
        
        Args:
            positions: 坐标列表
            delay: 延迟时间
            randomize: 是否随机化延迟
            
        Returns:
            点击数量
        """
        try:
            self._log_operation(f"批量点击坐标: {len(positions)} 个位置")
            
            count = batch_click(positions, delay, randomize)
            
            self._log_operation(f"✅ 批量点击完成: {count} 个位置")
            return count
            
        except Exception as e:
            self._log_operation(f"❌ 批量点击异常: {e}")
            self.error_count += 1
            return 0
    
    def crazy_click_at(self, x: int, y: int,
                       groups: int = 6,
                       clicks_per_group: int = 100) -> None:
        """
        疯狂点击指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            groups: 分组数
            clicks_per_group: 每组点击数
        """
        try:
            self._log_operation(f"疯狂点击: ({x}, {y}), {groups}组x{clicks_per_group}次")
            
            crazy_click(x, y, groups, clicks_per_group)
            
            self._log_operation(f"✅ 疯狂点击完成")
            
        except Exception as e:
            self._log_operation(f"❌ 疯狂点击异常: {e}")
            self.error_count += 1
    
    def scroll_area(self, direction: str, amount: int, 
                   x: Optional[int] = None, y: Optional[int] = None) -> None:
        """
        滚动指定区域
        
        Args:
            direction: 滚动方向 ('up', 'down')
            amount: 滚动量（像素）
            x: X坐标
            y: Y坐标
        """
        try:
            self._log_operation(f"智能滚动: {direction} {amount}像素")
            
            smart_scroll(direction, amount, x=x, y=y)
            
            self._log_operation(f"✅ 滚动完成")
            
        except Exception as e:
            self._log_operation(f"❌ 滚动异常: {e}")
            self.error_count += 1
    
    def sleep(self, duration: float, reason: str = ""):
        """
        等待指定时间
        
        Args:
            duration: 等待时间（秒）
            reason: 等待原因
        """
        reason_text = f" ({reason})" if reason else ""
        self._log_operation(f"等待 {duration}秒{reason_text}")
        time.sleep(duration)
    
    def debug_template(self, template_path: str, confidence: float = 0.8):
        """
        调试模板匹配
        
        Args:
            template_path: 模板路径
            confidence: 置信度
        """
        if self.debug_mode:
            self._log_operation(f"启动模板调试: {template_path}")
            debug_template_match(template_path, confidence)
        else:
            self.logger.info("调试模式未启用，跳过模板调试")
    
    def test_template_confidence(self, template_path: str, 
                               min_conf: float = 0.6,
                               max_conf: float = 0.95) -> Dict[float, int]:
        """
        测试模板在不同置信度下的匹配结果
        
        Args:
            template_path: 模板路径
            min_conf: 最小置信度
            max_conf: 最大置信度
            
        Returns:
            测试结果字典
        """
        self._log_operation(f"批量置信度测试: {template_path}")
        
        results = batch_confidence_test(template_path, (min_conf, max_conf))
        
        self._log_operation(f"✅ 置信度测试完成，测试点数: {len(results)}")
        return results
    
    def with_config(self, **config_overrides):
        """
        创建临时配置覆盖上下文
        
        Args:
            **config_overrides: 配置覆盖项
            
        Returns:
            配置上下文管理器
        """
        return with_config_override(**config_overrides)
    
    def _log_operation(self, message: str):
        """记录操作日志"""
        timestamp = time.time()
        self.execution_log.append((timestamp, message))
        self.logger.info(f"[{self.name}] {message}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        
        return {
            "name": self.name,
            "duration": duration,
            "error_count": self.error_count,
            "total_operations": len(self.execution_log),
            "success_rate": (len(self.execution_log) - self.error_count) / max(len(self.execution_log), 1),
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class SimpleWorkflow(WorkflowBase):
    """简单工作流基类"""
    
    def __init__(self, name: str = None, debug_mode: bool = False):
        super().__init__(name, debug_mode)
    
    def run(self) -> bool:
        """默认实现，子类可重写"""
        self.logger.info(f"执行简单工作流: {self.name}")
        return True