# RPA自动化框架

一个基于PyAutoGUI、OpenCV和Win32API的通用RPA（机器人流程自动化）框架，专为Windows平台设计，提供完整的鼠标、键盘、图像识别和窗口操作功能。

## 🚀 主要特性

- **多种元素定位方式**：坐标定位、图像识别、窗口句柄、OCR文本识别
- **完整的鼠标操作**：移动、点击、拖拽、滚轮、相对操作
- **丰富的键盘功能**：文本输入、快捷键、特殊按键、组合操作
- **智能等待机制**：元素等待、图像等待、条件等待、重试机制
- **模块化设计**：各功能独立封装，易于扩展和维护
- **完整的日志系统**：操作记录、错误追踪、调试信息
- **配置管理**：灵活的配置系统，支持不同环境

## 📋 系统要求

- **操作系统**：Windows 10/11
- **Python版本**：3.7+
- **依赖库**：见requirements.txt

## 🛠️ 安装指南

### 1. 克隆项目
```bash
git clone <repository-url>
cd 小新rpa
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv .env
.env\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 验证安装
```bash
cd rpa_framework
python main.py
```

## 📁 项目结构

```
rpa_framework/
├── core/                   # 核心功能模块
│   ├── locator.py         # 元素定位
│   ├── mouse.py           # 鼠标操作
│   ├── keyboard.py        # 键盘操作
│   ├── waiter.py          # 等待和验证
│   └── utils.py           # 工具函数
├── config/                # 配置管理
│   └── settings.py        # 配置文件
├── workflows/             # 业务流程
│   ├── wechat/           # 微信相关
│   └── email/            # 邮件相关
├── logs/                  # 日志目录
├── templates/             # 图像模板库
├── main.py               # 主程序入口
└── requirements.txt      # 依赖清单
```

## 🎯 快速开始

### 基础使用示例

```python
from rpa_framework.core.mouse import mouse
from rpa_framework.core.keyboard import keyboard
from rpa_framework.core.waiter import waiter

# 鼠标操作
mouse.move_to(500, 300)  # 移动鼠标
mouse.click()            # 点击
mouse.double_click(100, 200)  # 双击指定位置

# 键盘操作
keyboard.type_text("Hello RPA!")  # 输入文本
keyboard.hotkey('ctrl', 'c')      # 快捷键
keyboard.press_key('enter')       # 按键

# 等待操作
waiter.sleep(2)  # 等待2秒
```

### 图像识别示例

```python
from rpa_framework.core.locator import ImageLocator
from rpa_framework.core.waiter import wait_for_image

locator = ImageLocator()

# 截取屏幕
locator.take_screenshot("screen.png")

# 查找图像
location = locator.find_image("button.png", confidence=0.8)
if location:
    mouse.click(location[0], location[1])

# 等待图像出现
location = wait_for_image("dialog.png", timeout=10)
```

### 窗口操作示例

```python
from rpa_framework.core.locator import WindowLocator

window_locator = WindowLocator()

# 查找窗口
windows = window_locator.find_windows_by_title("记事本")
if windows:
    window_handle = windows[0]
    
    # 激活窗口
    window_locator.activate_window(window_handle)
    
    # 移动窗口
    window_locator.move_window(window_handle, 100, 100)
```

## 🔧 核心模块详解

### 1. 元素定位模块 (locator.py)

支持多种定位策略：

- **坐标定位**：直接使用屏幕坐标
- **图像定位**：基于OpenCV的模板匹配
- **窗口定位**：使用Win32API操作窗口
- **OCR定位**：文本识别定位（可选）

### 2. 鼠标操作模块 (mouse.py)

完整的鼠标控制功能：

```python
# 基本操作
mouse.move_to(x, y, duration=0.5)
mouse.click(x, y, button='left')
mouse.double_click(x, y)
mouse.right_click(x, y)

# 拖拽操作
mouse.drag_to(start_x, start_y, end_x, end_y)
mouse.drag_relative(dx, dy)

# 滚轮操作
mouse.scroll(clicks=3)  # 向上滚动
mouse.scroll(clicks=-3) # 向下滚动
```

### 3. 键盘操作模块 (keyboard.py)

丰富的键盘输入功能：

```python
# 文本输入
keyboard.type_text("Hello World")
keyboard.type_with_delay("Slow typing", char_delay=0.1)

# 按键操作
keyboard.press_key('enter')
keyboard.hotkey('ctrl', 'alt', 'delete')

# 便捷操作
keyboard.copy()
keyboard.paste()
keyboard.select_all()
keyboard.clear_text()

# IME输入法控制（Windows专用）
# 确保英文输入环境
original_status = keyboard.ensure_english_input()
try:
    keyboard.type_text("English text input")
finally:
    # 恢复原始输入法状态
    keyboard.restore_ime_status(original_status)

# 手动控制输入法状态
keyboard.set_ime_status(False)  # 关闭输入法
keyboard.set_ime_status(True)   # 开启输入法

# 获取当前输入法状态
status = keyboard.get_ime_status()
print(f"输入法状态: {'开启' if status else '关闭'}")
```

### 4. 等待验证模块 (waiter.py)

智能等待和重试机制：

```python
# 等待图像出现
location = waiter.wait_for_image("button.png", timeout=10)

# 等待条件满足
def check_condition():
    return mouse.get_position()[0] > 500

waiter.wait_until(check_condition, timeout=5)

# 重试操作
result = waiter.wait_and_retry(risky_operation, max_retries=3)
```

## 📝 配置说明

框架支持通过配置文件自定义行为：

```python
from rpa_framework.config.settings import config

# 获取配置
timeout = config.get('default_timeout', 10)
confidence = config.get('image_confidence', 0.8)

# 设置配置
config.set('custom_setting', 'value')
config.save()
```

### IME输入法控制配置

在`config/settings.yaml`中配置IME控制行为：

```yaml
keyboard:
  ime_control:
    enabled: true          # 启用IME控制功能
    fallback_enabled: true # 启用降级方案（快捷键）
    debug_mode: false      # 调试模式
    auto_restore: true     # 自动恢复输入法状态
```

**配置说明**：
- `enabled`: 控制是否启用IME控制功能
- `fallback_enabled`: 当IMM32 API不可用时是否使用快捷键降级方案
- `debug_mode`: 启用后会输出详细的调试信息
- `auto_restore`: 自动恢复输入法状态到操作前的状态

## 🚀 扩展开发

### 创建自定义工作流

```python
# workflows/custom/my_workflow.py
from rpa_framework.core import mouse, keyboard, waiter

class MyWorkflow:
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
    
    def execute(self):
        """执行自定义流程"""
        try:
            # 你的自动化逻辑
            mouse.click(100, 100)
            keyboard.type_text("Custom workflow")
            waiter.sleep(1)
            
            self.logger.info("工作流执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return False
```

### 添加新的定位策略

```python
# 继承基础定位器
from rpa_framework.core.locator import BaseLocator

class CustomLocator(BaseLocator):
    def find_element_by_custom_method(self, params):
        """自定义定位方法"""
        # 实现你的定位逻辑
        pass
```

## 🐛 故障排除

### 常见问题

1. **导入错误**
   - 确保已安装所有依赖包
   - 检查Python路径配置

2. **图像识别失败**
   - 调整confidence参数（建议0.7-0.9）
   - 确保模板图像清晰
   - 检查屏幕分辨率和缩放设置

3. **窗口操作失败**
   - 确保目标程序正在运行
   - 检查窗口标题是否正确
   - 以管理员权限运行

4. **权限问题**
   - 某些应用需要管理员权限
   - 检查防病毒软件设置

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 截图调试
locator.take_screenshot("debug.png")

# 获取当前鼠标位置
pos = mouse.get_position()
print(f"鼠标位置: {pos}")
```
