"""
企业微信专用异常类 - 最小化版本
避免复杂的依赖关系
"""


class RpaException(Exception):
    """RPA框架基础异常类"""
    pass


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