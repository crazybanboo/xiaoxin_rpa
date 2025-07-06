# 背景
文件名：2025-01-14_1_wechat-half-auto.md
创建于：2025-01-14_11:51:02
创建者：用户
主分支：main
任务分支：task/wechat-half-auto_2025-01-14_1
Yolo模式：Off

# 任务描述
实现企业微信半自动化脚本，主要功能包括：
1. 通过进程名称检测正在运行的企业微信进程
2. 获取企业微信窗口的大小和位置信息（不修改窗口）
3. 提供图像识别、定位器、鼠标操作等接口供用户自定义业务逻辑
4. 实现多选框发送消息的基础操作接口
5. 手动运行，执行一次完成一整套发送流程

# 项目概览
- 目标：构建企业微信半自动化操作脚本
- 技术栈：PyAutoGUI + OpenCV + Win32API + psutil
- 平台：Windows专用
- 接口：提供简洁的API接口供用户调用
- 架构：基于现有RPA框架扩展企业微信专用功能

⚠️ 警告：永远不要修改此部分 ⚠️
核心RIPER-5协议规则：
- 必须在每个响应开头声明当前模式
- EXECUTE模式必须100%遵循计划
- REVIEW模式必须标记所有偏差
- 未经明确许可不能在模式间转换
- 代码质量标准：完整上下文、错误处理、标准命名
⚠️ 警告：永远不要修改此部分 ⚠️

# 分析
基于用户需求分析：
1. 企业微信进程检测：需要通过进程名称（WXWork.exe等）找到正在运行的企业微信
2. 窗口信息获取：使用Win32 API获取窗口大小、位置，不需要修改窗口
3. 操作接口提供：封装定位器、图像识别器、鼠标操作等接口
4. 业务逻辑分离：框架提供基础接口，用户自定义具体的多选和发送逻辑

技术要点：
- 使用psutil库进行进程检测
- 使用win32gui获取窗口信息
- 扩展现有的WindowLocator功能
- 提供企业微信专用的操作接口

# 提议的解决方案
采用分层架构设计：

## 核心组件设计
1. **WechatProcessDetector**：企业微信进程检测器
   - 检测企业微信是否运行
   - 获取进程信息和PID
   - 支持多实例检测

2. **WechatWindowManager**：企业微信窗口管理器
   - 获取窗口句柄
   - 获取窗口大小和位置
   - 提供窗口区域计算

3. **WechatOperationInterface**：企业微信操作接口
   - 封装定位器使用方法
   - 封装图像识别功能
   - 封装鼠标操作方法

4. **WechatHalfAuto**：主控制器
   - 整合所有组件
   - 提供统一的API接口
   - 实现完整的自动化流程

## 技术实现方案
- 进程检测：使用psutil.process_iter()枚举进程
- 窗口操作：扩展现有WindowLocator类
- 图像识别：使用现有ImageLocator类
- 鼠标操作：使用现有MouseController类
- 配置管理：扩展现有配置系统

# 当前执行步骤："阶段1-3已完成，等待用户确认"

# 任务进度

[2025-01-14 14:30:00]
- 已修改：requirements.txt (已存在psutil依赖)
- 已修改：rpa_framework/core/wechat_detector.py (新建)
- 已修改：rpa_framework/core/locator.py (扩展WindowLocator)
- 已修改：rpa_framework/config/settings.py (添加企业微信配置)
- 更改：完成阶段一基础模块实现 - 企业微信进程检测器、窗口信息获取功能扩展、配置项添加
- 原因：为企业微信半自动化脚本建立基础架构
- 阻碍因素：无
- 状态：已确认

[2025-01-14 15:45:00]
- 已修改：rpa_framework/workflows/wechat/wechat_operations.py (新建)
- 已修改：rpa_framework/workflows/wechat/exceptions.py (新建)
- 已修改：templates/wechat/ (新建目录)
- 已修改：rpa_framework/workflows/wechat/__init__.py (新建)
- 已修改：rpa_framework/workflows/wechat/wechat-half-auto.py (重构)
- 更改：完成阶段二操作接口实现 - 企业微信操作接口、异常类、模板目录、模块初始化文件、主控制器重构
- 原因：实现企业微信操作的封装接口和主控制逻辑
- 阻碍因素：部分类型错误和API调用问题需要在实际使用中调试
- 状态：未确认

[2025-01-14 16:00:00]
- 已修改：rpa_framework/main.py (添加企业微信演示功能)
- 已修改：rpa_framework/workflows/wechat/__init__.py (添加延迟导入)
- 更改：完成阶段三主控制器集成 - 在主框架中添加企业微信演示功能
- 原因：将企业微信功能集成到主框架演示系统中
- 阻碍因素：导入路径问题需要在实际运行时调试
- 状态：未确认

# 最终审查
[待完成]

# 详细实施计划

## 实施架构设计

### 1. 企业微信进程检测模块
**文件位置**: `rpa_framework/core/wechat_detector.py`
**核心功能**:
- 枚举所有运行进程，查找企业微信进程
- 支持多种企业微信进程名称（WXWork.exe、企业微信.exe等）
- 获取进程PID、内存使用情况等信息
- 提供进程状态监控功能

### 2. 窗口信息管理模块
**文件位置**: `rpa_framework/core/locator.py`（扩展现有WindowLocator）
**核心功能**:
- 通过进程PID获取对应窗口句柄
- 获取窗口矩形区域（left, top, right, bottom）
- 计算窗口宽度、高度、中心点坐标
- 提供相对坐标转换功能
- 添加窗口状态检测（最大化、最小化、正常）

### 3. 企业微信操作接口模块
**文件位置**: `rpa_framework/workflows/wechat/wechat_operations.py`
**核心功能**:
- 封装图像识别操作（按钮、多选框识别）
- 封装鼠标操作（点击、多选、拖拽）
- 封装键盘操作（文本输入、快捷键）
- 提供组合操作方法（多选群聊、发送消息）

### 4. 主控制器模块
**文件位置**: `rpa_framework/workflows/wechat/wechat-half-auto.py`（重构现有文件）
**核心功能**:
- 整合所有子模块
- 提供统一的API接口
- 实现完整的自动化流程控制
- 错误处理和日志记录

## 核心API设计规范

### 1. 进程检测API
```python
class WechatProcessDetector:
    def find_wechat_processes(self) -> List[ProcessInfo]
    def get_main_wechat_process(self) -> Optional[ProcessInfo]
    def is_wechat_running(self) -> bool
    def get_process_window_handle(self, pid: int) -> Optional[int]
```

### 2. 窗口管理API
```python
class WechatWindowManager:
    def get_window_info(self, hwnd: int) -> WindowInfo
    def get_window_size(self, hwnd: int) -> Tuple[int, int]
    def get_window_position(self, hwnd: int) -> Tuple[int, int]
    def get_window_center(self, hwnd: int) -> Tuple[int, int]
    def convert_to_relative_coords(self, x: int, y: int, hwnd: int) -> Tuple[float, float]
```

### 3. 操作接口API
```python
class WechatOperationInterface:
    def find_button_by_template(self, template_path: str) -> Optional[Tuple[int, int]]
    def find_checkbox_by_template(self, template_path: str) -> List[Tuple[int, int]]
    def click_at_position(self, x: int, y: int) -> bool
    def multi_select_click(self, positions: List[Tuple[int, int]]) -> bool
    def type_message(self, message: str) -> bool
    def send_message(self) -> bool
```

### 4. 主控制器API
```python
class WechatHalfAuto:
    def initialize(self) -> bool
    def get_wechat_window_info(self) -> WindowInfo
    def get_locator(self) -> CompositeLocator
    def get_image_recognizer(self) -> ImageLocator
    def get_mouse_controller(self) -> MouseController
    def get_keyboard_controller(self) -> KeyboardController
    def execute_multi_chat_send(self, message: str, chat_templates: List[str]) -> bool
```

## 数据结构设计

### 1. 进程信息结构
```python
@dataclass
class ProcessInfo:
    pid: int
    name: str
    exe_path: str
    memory_usage: int
    cpu_percent: float
    create_time: float
```

### 2. 窗口信息结构
```python
@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    width: int
    height: int
    center: Tuple[int, int]
    is_visible: bool
    is_maximized: bool
```

### 3. 操作结果结构
```python
@dataclass
class OperationResult:
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
```

## 配置管理扩展

### 1. 企业微信配置
**文件位置**: `rpa_framework/config/settings.py`（扩展现有配置）
**配置项**:
```python
@dataclass
class WechatSettings:
    process_names: List[str] = field(default_factory=lambda: ["WXWork.exe", "企业微信.exe"])
    window_detection_timeout: float = 10.0
    operation_delay: float = 0.5
    template_confidence: float = 0.8
    multi_select_interval: float = 0.2
    message_send_delay: float = 1.0
```

### 2. 模板路径配置
```python
@dataclass
class WechatTemplateSettings:
    template_dir: str = "templates/wechat"
    button_templates: Dict[str, str] = field(default_factory=dict)
    checkbox_templates: Dict[str, str] = field(default_factory=dict)
```

## 错误处理策略

### 1. 异常类型定义
```python
class WechatNotFoundError(RpaException):
    """企业微信未找到异常"""
    pass

class WechatWindowError(RpaException):
    """企业微信窗口操作异常"""
    pass

class WechatOperationError(RpaException):
    """企业微信操作异常"""
    pass
```

### 2. 错误处理机制
- 进程检测失败：提供重试机制和用户提示
- 窗口操作失败：记录详细错误信息和截图
- 图像识别失败：提供降级方案和手动定位选项
- 操作执行失败：提供回滚机制和状态恢复

## 日志记录规范

### 1. 日志级别定义
- DEBUG：详细的操作步骤和参数
- INFO：关键操作节点和状态变化
- WARNING：非致命错误和降级操作
- ERROR：操作失败和异常情况
- CRITICAL：系统级错误和不可恢复错误

### 2. 日志内容规范
- 操作时间戳
- 操作类型和参数
- 执行结果和耗时
- 错误信息和堆栈跟踪
- 相关截图路径

## 实施清单

### 阶段一：基础模块实现
1. 扩展requirements.txt，添加psutil依赖
2. 创建rpa_framework/core/wechat_detector.py - 企业微信进程检测器
3. 扩展rpa_framework/core/locator.py - 添加窗口信息获取功能
4. 扩展rpa_framework/config/settings.py - 添加企业微信配置项

### 阶段二：操作接口实现
5. 创建rpa_framework/workflows/wechat/wechat_operations.py - 企业微信操作接口
6. 创建rpa_framework/workflows/wechat/exceptions.py - 企业微信专用异常类
7. 创建templates/wechat/目录 - 图像模板存储目录

### 阶段三：主控制器实现
8. 重构rpa_framework/workflows/wechat/wechat-half-auto.py - 实现主控制器
9. 创建rpa_framework/workflows/wechat/__init__.py - 模块初始化文件
10. 更新rpa_framework/main.py - 添加企业微信演示功能

### 阶段四：测试和文档
11. 创建测试用例和使用示例
12. 更新README.md - 添加企业微信功能说明
13. 创建用户使用指南和API文档

## 质量保证措施

### 1. 代码质量标准
- 完整的类型注解
- 详细的文档字符串
- 统一的命名规范
- 完整的错误处理
- 充分的日志记录

### 2. 测试策略
- 单元测试：每个模块的核心功能
- 集成测试：模块间的协作功能
- 端到端测试：完整的自动化流程
- 性能测试：响应时间和资源使用

### 3. 文档规范
- API文档：详细的接口说明和使用示例
- 用户指南：操作步骤和注意事项
- 开发文档：架构设计和扩展指南
- 故障排除：常见问题和解决方案

## 部署和维护

### 1. 部署要求
- Windows 10/11操作系统
- Python 3.7+环境
- 企业微信客户端已安装
- 必要的系统权限

### 2. 维护计划
- 定期更新图像模板
- 监控企业微信版本变化
- 优化性能和稳定性
- 收集用户反馈和改进建议

这个实施计划提供了完整的技术架构、API设计、实施步骤和质量保证措施，确保企业微信半自动化脚本的成功实现。 