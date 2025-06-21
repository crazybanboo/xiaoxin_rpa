# 背景
文件名：2025-06-22_1_rpa-framework-setup.md
创建于：2025-06-22_00:13:21
创建者：用户
主分支：main
任务分支：task/rpa-framework-setup_2025-06-22_1
Yolo模式：Off

# 任务描述
搭建通用RPA框架基础结构，实现企业微信自动拉群功能的底层支撑。框架需要支持基于PyAutoGUI、OpenCV和Win32API的元素定位、鼠标键盘操作、等待验证等核心功能。设计为通用框架，便于扩展到其他RPA业务场景。

# 项目概览
- 目标：构建通用RPA操作框架
- 技术栈：PyAutoGUI + OpenCV + Win32API
- 平台：Windows专用
- 接口：纯命令行工具
- 架构：模块化设计，支持多业务流程扩展

⚠️ 警告：永远不要修改此部分 ⚠️
核心RIPER-5协议规则：
- 必须在每个响应开头声明当前模式
- EXECUTE模式必须100%遵循计划
- REVIEW模式必须标记所有偏差
- 未经明确许可不能在模式间转换
- 代码质量标准：完整上下文、错误处理、标准命名
⚠️ 警告：永远不要修改此部分 ⚠️

# 分析
当前工作空间为空项目，需要从零开始构建RPA框架。

核心技术需求分析：
1. 元素定位：需要多种定位策略（坐标、图像识别、Win32API）
2. 鼠标操作：移动、点击、拖拽、滚轮等基础操作
3. 键盘操作：文本输入、快捷键、特殊按键
4. 等待验证：元素等待、超时处理、操作验证
5. 工具函数：截图、日志、配置、异常处理

框架设计原则：
- 模块化：每个功能独立封装
- 可扩展：支持多业务场景
- 易用性：提供简洁API接口
- 可靠性：完整的错误处理和日志

# 提议的解决方案
采用分层模块化架构：
- core层：提供基础RPA操作能力
- config层：统一配置管理
- workflows层：业务流程实现
- 工具层：日志、截图、异常处理

技术选型：
- PyAutoGUI：主要操作库，提供跨平台基础能力
- OpenCV：图像识别和模板匹配，增强定位可靠性
- Win32API：Windows系统底层控制，补充PyAutoGUI不足
- Python logging：统一日志管理

# 当前执行步骤："1. 创建项目目录结构"

# 任务进度

# 最终审查

# 详细实施计划

## 项目结构
```
rpa_framework/
├── core/
│   ├── __init__.py
│   ├── locator.py      # 元素定位
│   ├── mouse.py        # 鼠标操作
│   ├── keyboard.py     # 键盘操作
│   ├── waiter.py       # 等待和验证
│   └── utils.py        # 工具函数
├── config/
│   ├── __init__.py
│   └── settings.py     # 配置管理
├── logs/               # 日志目录
├── templates/          # 图像模板库
├── workflows/          # 业务流程目录
│   ├── wechat/         # 企业微信相关流程
│   ├── email/          # 邮件相关流程
│   └── ...             # 其他业务流程
├── main.py            # 主程序入口
├── requirements.txt   # 依赖包
└── README.md          # 项目说明
```

## 核心功能模块设计

### 1. locator.py - 元素定位
- 坐标定位：直接坐标点击
- 图像定位：OpenCV模板匹配
- 窗口定位：Win32API窗口句柄
- OCR定位：文本识别定位
- 组合定位：多种策略结合

### 2. mouse.py - 鼠标操作
- 移动：move_to(x, y)
- 点击：click(), double_click(), right_click()
- 拖拽：drag_to(start, end)
- 滚轮：scroll(direction, clicks)
- 相对操作：relative_move(), relative_click()

### 3. keyboard.py - 键盘操作
- 文本输入：type_text(text)
- 快捷键：hotkey(keys)
- 特殊按键：press_key(key)
- 组合操作：key_combination()

### 4. waiter.py - 等待和验证
- 元素等待：wait_for_element()
- 图像等待：wait_for_image()
- 条件等待：wait_until()
- 超时处理：timeout_handler()

### 5. utils.py - 工具函数
- 截图：screenshot(), screenshot_region()
- 日志：setup_logger(), log_operation()
- 配置：load_config(), save_config()
- 异常：RpaException, error_handler()

## 实施清单
1. 创建项目目录结构
2. 创建requirements.txt文件，定义项目依赖
3. 实现core/utils.py - 基础工具函数
4. 实现config/settings.py - 配置管理
5. 实现core/locator.py - 元素定位功能
6. 实现core/mouse.py - 鼠标操作功能
7. 实现core/keyboard.py - 键盘操作功能
8. 实现core/waiter.py - 等待和验证功能
9. 创建main.py - 主程序和使用示例
10. 创建README.md - 项目说明文档 