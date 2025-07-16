"""
RPA框架 - 鼠标操作辅助工具
提供实用的高级鼠标操作，避免过度封装

设计原则：
1. 函数式设计，避免状态管理
2. 直接封装常用操作模式
3. 最小化参数和配置
4. 异常处理而非复杂的结果包装
"""

import time
import random
from typing import List, Tuple, Optional, Union
from .mouse import MouseController
from .locator import CompositeLocator
from .utils import logger, RpaException


# 全局实例（延迟初始化）
_mouse_controller = None
_locator = None


def _get_mouse_controller():
    """获取全局鼠标控制器实例"""
    global _mouse_controller
    if _mouse_controller is None:
        _mouse_controller = MouseController()
    return _mouse_controller


def _get_locator():
    """获取全局定位器实例"""
    global _locator
    if _locator is None:
        _locator = CompositeLocator()
    return _locator


def find_and_click(template_path: str, 
                   confidence: float = 0.8,
                   region: Optional[Tuple[int, int, int, int]] = None,
                   click_offset: Tuple[int, int] = (0, 0),
                   timeout: float = 5.0) -> bool:
    """
    查找模板并点击
    
    Args:
        template_path: 模板图片路径
        confidence: 匹配置信度
        region: 搜索区域 (left, top, width, height)
        click_offset: 点击偏移 (dx, dy)
        timeout: 超时时间（秒）
        
    Returns:
        是否成功点击
        
    Raises:
        TemplateNotFound: 模板未找到
        RpaException: 其他RPA操作错误
    """
    locator = _get_locator()
    mouse = _get_mouse_controller()
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # 查找模板
            result = locator.image_locator.locate_by_template(
                template_path, confidence, region
            )
            
            if result:
                left, top, right, bottom = result
                # 计算中心点
                center_x = (left + right) // 2 + click_offset[0]
                center_y = (top + bottom) // 2 + click_offset[1]
                
                # 点击
                mouse.click(center_x, center_y)
                logger.info(f"成功点击模板: {template_path} at ({center_x}, {center_y})")
                return True
            
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"查找并点击模板时发生错误: {e}")
            raise RpaException(f"查找并点击模板失败: {e}")
    
    # 超时未找到
    raise TemplateNotFound(f"超时未找到模板: {template_path}")


def find_all_and_click(template_path: str,
                       confidence: float = 0.8,
                       region: Optional[Tuple[int, int, int, int]] = None,
                       click_delay: float = 0.5,
                       max_clicks: int = 10) -> int:
    """
    查找所有匹配的模板并批量点击
    
    Args:
        template_path: 模板图片路径
        confidence: 匹配置信度
        region: 搜索区域
        click_delay: 点击间隔
        max_clicks: 最大点击数量
        
    Returns:
        实际点击的数量
        
    Raises:
        TemplateNotFound: 模板未找到
    """
    locator = _get_locator()
    mouse = _get_mouse_controller()
    
    # 查找所有匹配项
    results = locator.image_locator.locate_all_by_template(
        template_path, confidence, region, max_results=max_clicks
    )
    
    if not results:
        raise TemplateNotFound(f"未找到模板: {template_path}")
    
    click_count = 0
    for left, top, right, bottom, match_confidence in results:
        # 计算中心点
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        # 点击
        mouse.click(center_x, center_y)
        click_count += 1
        
        logger.debug(f"点击模板 {template_path} at ({center_x}, {center_y}), 置信度: {match_confidence:.3f}")
        
        # 延迟
        if click_count < len(results):
            time.sleep(click_delay)
    
    logger.info(f"批量点击完成: {template_path}, 点击数量: {click_count}")
    return click_count


def batch_click(positions: List[Tuple[int, int]], 
                delay: float = 0.5,
                randomize_delay: bool = True) -> int:
    """
    批量点击指定位置
    
    Args:
        positions: 坐标列表 [(x, y), ...]
        delay: 基础延迟时间
        randomize_delay: 是否随机化延迟
        
    Returns:
        实际点击的数量
    """
    mouse = _get_mouse_controller()
    
    click_count = 0
    for x, y in positions:
        mouse.click(x, y)
        click_count += 1
        
        # 计算延迟时间
        if click_count < len(positions):
            actual_delay = delay
            if randomize_delay:
                # 延迟时间随机化 ±20%
                actual_delay = delay * random.uniform(0.8, 1.2)
            time.sleep(actual_delay)
    
    logger.info(f"批量点击完成: {click_count} 个位置")
    return click_count


def special_click_sequence(positions: List[Tuple[int, int]], 
                          count: int = 3,
                          click_delay: float = 0.01,
                          position_delay: float = 0.5) -> None:
    """
    特殊点击序列：在每个位置连续点击多次
    
    Args:
        positions: 坐标列表
        count: 每个位置的点击次数
        click_delay: 同一位置连续点击的延迟
        position_delay: 不同位置之间的延迟
    """
    mouse = _get_mouse_controller()
    
    for i, (x, y) in enumerate(positions):
        # 在当前位置连续点击
        for j in range(count):
            mouse.click(x, y)
            if j < count - 1:
                time.sleep(click_delay)
        
        logger.debug(f"完成位置 ({x}, {y}) 的 {count} 次点击")
        
        # 位置间延迟
        if i < len(positions) - 1:
            time.sleep(position_delay)
    
    logger.info(f"特殊点击序列完成: {len(positions)} 个位置，每个位置 {count} 次")


def crazy_click(x: int, y: int, 
                groups: int = 6, 
                clicks_per_group: int = 100,
                group_delay: float = 0.1,
                click_delay: float = 0.01) -> None:
    """
    疯狂点击：分组高频点击
    
    Args:
        x: 点击X坐标
        y: 点击Y坐标
        groups: 分组数量
        clicks_per_group: 每组点击次数
        group_delay: 组间延迟
        click_delay: 点击间延迟
    """
    mouse = _get_mouse_controller()
    
    total_clicks = 0
    for group in range(groups):
        logger.debug(f"开始第 {group + 1} 组点击")
        
        for click in range(clicks_per_group):
            mouse.click(x, y)
            total_clicks += 1
            
            if click < clicks_per_group - 1:
                time.sleep(click_delay)
        
        # 组间延迟
        if group < groups - 1:
            time.sleep(group_delay)
    
    logger.info(f"疯狂点击完成: 总计 {total_clicks} 次点击")


def smart_scroll(direction: str, 
                 amount: int, 
                 steps: int = 3,
                 x: Optional[int] = None,
                 y: Optional[int] = None) -> None:
    """
    智能滚动：分步平滑滚动
    
    Args:
        direction: 滚动方向 ('up', 'down')
        amount: 滚动总量（像素）
        steps: 分解步数
        x: 滚动位置X坐标
        y: 滚动位置Y坐标
    """
    mouse = _get_mouse_controller()
    
    # 计算滚动方向
    if direction.lower() == 'up':
        scroll_amount = amount
    elif direction.lower() == 'down':
        scroll_amount = -amount
    else:
        raise ValueError(f"无效的滚动方向: {direction}")
    
    # 分步滚动
    step_amount = scroll_amount // steps
    remainder = scroll_amount % steps
    
    for i in range(steps):
        current_amount = step_amount + (remainder if i == steps - 1 else 0)
        
        # 转换为滚轮点击次数（大概每次120像素）
        clicks = current_amount // 120
        if clicks != 0:
            mouse.scroll(clicks, x, y)
        
        if i < steps - 1:
            time.sleep(0.1)
    
    logger.info(f"智能滚动完成: {direction} {amount}像素，分{steps}步")


def wait_and_find_template(template_paths: List[str],
                          confidence: float = 0.8,
                          timeout: float = 10.0,
                          check_interval: float = 0.5) -> Optional[Tuple[str, Tuple[int, int, int, int]]]:
    """
    等待并查找多个模板中的任意一个
    
    Args:
        template_paths: 模板路径列表
        confidence: 匹配置信度
        timeout: 超时时间
        check_interval: 检查间隔
        
    Returns:
        (匹配的模板路径, 匹配区域) 或 None
    """
    locator = _get_locator()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        for template_path in template_paths:
            try:
                result = locator.image_locator.locate_by_template(
                    template_path, confidence
                )
                
                if result:
                    logger.info(f"找到模板: {template_path}")
                    return (template_path, result)
                    
            except Exception as e:
                logger.debug(f"查找模板 {template_path} 时出错: {e}")
                continue
        
        time.sleep(check_interval)
    
    logger.warning(f"超时未找到任何模板: {template_paths}")
    return None


def calculate_centers_from_rects(rects: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int]]:
    """
    从矩形区域计算中心点
    
    Args:
        rects: 矩形区域列表 [(left, top, right, bottom), ...]
        
    Returns:
        中心点列表 [(x, y), ...]
    """
    centers = []
    for left, top, right, bottom in rects:
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        centers.append((center_x, center_y))
    
    return centers


def find_template_centers(template_path: str,
                         confidence: float = 0.8,
                         region: Optional[Tuple[int, int, int, int]] = None,
                         max_results: int = 10) -> List[Tuple[int, int]]:
    """
    查找模板并返回所有匹配的中心点
    
    Args:
        template_path: 模板路径
        confidence: 匹配置信度
        region: 搜索区域
        max_results: 最大结果数
        
    Returns:
        中心点列表 [(x, y), ...]
        
    Raises:
        TemplateNotFound: 模板未找到
    """
    locator = _get_locator()
    
    # 查找所有匹配项
    results = locator.image_locator.locate_all_by_template(
        template_path, confidence, region, max_results=max_results
    )
    
    if not results:
        raise TemplateNotFound(f"未找到模板: {template_path}")
    
    # 计算中心点
    centers = []
    for left, top, right, bottom, match_confidence in results:
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        centers.append((center_x, center_y))
    
    logger.info(f"找到 {len(centers)} 个模板中心点: {template_path}")
    return centers


# 自定义异常
class TemplateNotFound(RpaException):
    """模板未找到异常"""
    pass


class MouseOperationError(RpaException):
    """鼠标操作错误异常"""
    pass