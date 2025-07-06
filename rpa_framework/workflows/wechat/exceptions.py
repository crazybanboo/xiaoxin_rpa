"""
企业微信专用异常类
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.utils import RpaException


class WechatNotFoundError(RpaException):
    """企业微信未找到异常"""
    pass


class WechatWindowError(RpaException):
    """企业微信窗口操作异常"""
    pass


class WechatOperationError(RpaException):
    """企业微信操作异常"""
    pass


class WechatProcessError(RpaException):
    """企业微信进程异常"""
    pass


class WechatTemplateError(RpaException):
    """企业微信模板异常"""
    pass 