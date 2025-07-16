# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive RPA (Robotic Process Automation) framework for Windows, specifically designed for automating WeChat Work (企业微信) operations. The framework provides a modular architecture with support for mouse control, keyboard input, image recognition, window management, and automated workflows.

## Core Architecture

### Main Components

- **Core Modules** (`rpa_framework/core/`):
  - `locator.py`: Multi-strategy element location (coordinates, image matching, window handles, OCR)
  - `mouse.py`: Complete mouse control (movement, clicking, dragging, scrolling)
  - `keyboard.py`: Keyboard operations with IME support for Chinese/English input switching
  - `waiter.py`: Smart waiting mechanisms and retry logic
  - `utils.py`: Utilities including logging, configuration, and screen capture
  - `wechat_detector.py`: WeChat-specific detection and automation helpers

- **Configuration System** (`rpa_framework/config/`):
  - `settings.py`: Comprehensive configuration management with dataclasses
  - `settings.yaml`: YAML configuration file for runtime settings

- **Workflow System** (`rpa_framework/workflows/`):
  - `wechat/`: WeChat Work automation workflows
    - `wechat_operations.py`: Core operation interface
    - `wechat_half_auto.py`: Semi-automatic and full-automatic messaging workflows
    - `exceptions.py`: Custom exception handling

- **Templates** (`rpa_framework/templates/`):
  - Image templates for visual recognition
  - WeChat-specific UI elements and buttons

## Development Commands

### Building the Application

The project uses Nuitka for building standalone executables:

```powershell
# Recommended: Lite build (stable, no OCR)
.\build_lite.ps1

# Full build with OCR (may have PyTorch compatibility issues)
.\build.ps1

# Alternative: PyInstaller build
.\build_pyinstaller.ps1
```

### Running the Application

```bash
# Run main application
cd rpa_framework
python main.py

# Run tests (if available)
python test.py
```

### Installing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Core dependencies include:
# - pyautogui (GUI automation)
# - opencv-python (image processing)
# - pywin32 (Windows API)
# - pillow (image handling)
# - numpy (numerical operations)
# - easyocr (OCR functionality)
# - nuitka (compilation)
```

## Key Design Patterns

### Singleton Pattern
- Used for global configuration (`settings`) and locator instances
- Ensures consistent state across the application

### Strategy Pattern
- Multiple locator strategies (coordinate, image, window, OCR)
- Unified interface through `CompositeLocator`

### Factory Pattern
- Logger factory (`RpaLogger.get_logger()`)
- Configuration factory functions

### Observer Pattern
- Global hotkey system for F12 termination
- Event-driven workflow management

## Important Configuration

### Image Recognition Settings
- Default confidence: 0.8
- Template matching method: TM_CCOEFF_NORMED
- Grayscale processing enabled by default

### WeChat Work Settings
- Window size: 1200x800
- Template confidence: 0.8
- Multi-select interval: 0.2s
- Message send delay: 1.0s

### Logging Configuration
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Colored console output
- Per-module log files + master log file
- Log rotation with 10MB max size, 5 backup files

## Development Guidelines

### Adding New Workflows
1. Create new workflow class in `workflows/` directory
2. Inherit from base patterns or implement operation interfaces
3. Use the global locator and controller instances
4. Implement proper error handling with custom exceptions
5. Add configuration options to `settings.py`

### Image Template Management
- Store templates in `templates/` with descriptive names
- Use PNG format for better accuracy
- Test templates at different screen resolutions
- Document template confidence requirements

### Error Handling
- Use custom exceptions from `workflows/wechat/exceptions.py`
- Implement retry logic with `WaitController`
- Screenshot on errors for debugging
- Log detailed error information

## Security Considerations

- Fail-safe mechanisms enabled by default
- Screenshot masking for sensitive data
- Maximum operation time limits
- F12 emergency termination

## Common Operations

### Image Recognition
```python
# Find and click an image
location = locator.image_locator.locate_by_template("button.png")
if location:
    mouse.click(location[0], location[1])
```

### Window Management
```python
# Find and activate WeChat window
window = locator.window_locator.find_window_by_title("企业微信")
if window:
    locator.window_locator.activate_window(window)
```

### Input Method Control
```python
# Switch to English input
keyboard.change_language(LanguageType.EN)
keyboard.type_text("English text")
keyboard.change_language(LanguageType.ZH)
```

## Testing

- Manual testing through `main.py` demo functions
- Template matching validation
- Window detection verification
- Input method switching tests

## Build Troubleshooting

- Use `build_lite.ps1` for most stable builds
- PyTorch/easyocr compatibility issues with Nuitka
- Ensure Visual C++ Redistributable is installed
- Run with administrator privileges if needed
- Check antivirus software exclusions

## File Structure Notes

- `main.py`: Entry point with menu system
- `logs/`: Auto-generated log files with date stamps
- `main.dist/`: Build output directory
- Template files are included in builds via `--include-data-dir`