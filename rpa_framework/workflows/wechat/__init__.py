"""
企业微信半自动化模块
"""
# 移除过度封装的WechatOperationInterface和OperationResult
from .exceptions import (
    WechatNotFoundError,
    WechatWindowError,
    WechatOperationError,
    WechatProcessError,
    WechatTemplateError
)

from .wechat_half_auto import WechatHalfAuto

__all__ = [
    'WechatNotFoundError',
    'WechatWindowError',
    'WechatOperationError',
    'WechatProcessError',
    'WechatTemplateError',
    'WechatHalfAuto'
] 