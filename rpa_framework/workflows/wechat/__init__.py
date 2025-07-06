"""
企业微信半自动化模块
"""
from .wechat_operations import WechatOperationInterface, OperationResult
from .exceptions import (
    WechatNotFoundError,
    WechatWindowError,
    WechatOperationError,
    WechatProcessError,
    WechatTemplateError
)

from .wechat_half_auto import WechatHalfAuto

__all__ = [
    'WechatOperationInterface',
    'OperationResult',
    'WechatNotFoundError',
    'WechatWindowError',
    'WechatOperationError',
    'WechatProcessError',
    'WechatTemplateError',
    'WechatHalfAuto'
] 