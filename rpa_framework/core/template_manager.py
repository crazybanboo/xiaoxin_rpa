"""
RPA框架 - 模板管理模块
提供模板文件的组织、查找和管理功能

功能特性：
1. 模板路径自动解析
2. 模板分组管理
3. 模板验证和检查
4. 模板搜索和发现
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict

from .utils import logger, RpaException
from ..config.settings import get_config


@dataclass
class TemplateInfo:
    """模板信息"""
    name: str
    path: str
    group: str
    description: str = ""
    confidence: float = 0.8
    grayscale: bool = True
    size: Tuple[int, int] = (0, 0)
    created_time: float = 0.0
    modified_time: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化模板管理器
        
        Args:
            template_dir: 模板目录路径
        """
        if template_dir is None:
            template_dir = get_config('general.template_dir', 'templates')
        
        self.template_dir = Path(template_dir)
        if not self.template_dir.is_absolute():
            # 相对于项目根目录
            project_root = Path(__file__).parent.parent
            self.template_dir = project_root / template_dir
        
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 模板注册表
        self.templates: Dict[str, TemplateInfo] = {}
        self.groups: Dict[str, List[str]] = {}
        
        # 缓存文件
        self.registry_file = self.template_dir / "template_registry.json"
        
        # 支持的图像格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        
        self.logger = logger
        
        # 加载现有模板
        self.scan_templates()
        self.load_registry()
    
    def scan_templates(self) -> int:
        """
        扫描模板目录，发现所有模板文件
        
        Returns:
            发现的模板数量
        """
        discovered = 0
        
        for root, dirs, files in os.walk(self.template_dir):
            root_path = Path(root)
            
            # 计算分组名（相对于模板根目录的路径）
            relative_path = root_path.relative_to(self.template_dir)
            group_name = str(relative_path) if relative_path != Path('.') else 'default'
            
            for file in files:
                file_path = root_path / file
                
                # 检查是否为支持的图像格式
                if file_path.suffix.lower() in self.supported_formats:
                    template_name = file_path.stem
                    
                    # 避免重复添加
                    if template_name not in self.templates:
                        template_info = self._create_template_info(
                            template_name, str(file_path), group_name
                        )
                        self.templates[template_name] = template_info
                        
                        # 添加到分组
                        if group_name not in self.groups:
                            self.groups[group_name] = []
                        if template_name not in self.groups[group_name]:
                            self.groups[group_name].append(template_name)
                        
                        discovered += 1
        
        self.logger.info(f"模板扫描完成，发现 {discovered} 个模板")
        return discovered
    
    def _create_template_info(self, name: str, path: str, group: str) -> TemplateInfo:
        """创建模板信息对象"""
        file_path = Path(path)
        
        # 获取文件信息
        stat = file_path.stat()
        
        # 尝试获取图像尺寸
        size = (0, 0)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                size = img.size
        except Exception:
            pass
        
        return TemplateInfo(
            name=name,
            path=str(file_path),
            group=group,
            size=size,
            created_time=stat.st_ctime,
            modified_time=stat.st_mtime
        )
    
    def get_template_path(self, template_name: str, group: Optional[str] = None) -> Optional[str]:
        """
        获取模板文件路径
        
        Args:
            template_name: 模板名称（支持相对路径）
            group: 指定分组
            
        Returns:
            模板文件的完整路径或None
        """
        # 如果是完整路径，直接返回
        if os.path.isabs(template_name):
            return template_name if Path(template_name).exists() else None
        
        # 如果包含路径分隔符，可能是相对路径
        if '/' in template_name or '\\' in template_name:
            full_path = self.template_dir / template_name
            return str(full_path) if full_path.exists() else None
        
        # 查找注册的模板
        template_info = self.templates.get(template_name)
        if template_info:
            if group is None or template_info.group == group:
                return template_info.path
        
        # 按文件名搜索（不包含扩展名）
        for ext in self.supported_formats:
            # 在指定分组中搜索
            if group:
                group_path = self.template_dir / group / f"{template_name}{ext}"
                if group_path.exists():
                    return str(group_path)
            
            # 在根目录搜索
            root_path = self.template_dir / f"{template_name}{ext}"
            if root_path.exists():
                return str(root_path)
            
            # 在所有子目录搜索
            for template_info in self.templates.values():
                if template_info.name == template_name:
                    if group is None or template_info.group == group:
                        return template_info.path
        
        self.logger.warning(f"未找到模板: {template_name}")
        return None
    
    def register_template(self, name: str, path: str, group: str = 'default',
                         description: str = "", confidence: float = 0.8,
                         tags: List[str] = None) -> bool:
        """
        注册模板
        
        Args:
            name: 模板名称
            path: 模板路径
            group: 分组名称
            description: 描述
            confidence: 推荐置信度
            tags: 标签列表
            
        Returns:
            是否注册成功
        """
        if not Path(path).exists():
            self.logger.error(f"模板文件不存在: {path}")
            return False
        
        template_info = self._create_template_info(name, path, group)
        template_info.description = description
        template_info.confidence = confidence
        template_info.tags = tags or []
        
        self.templates[name] = template_info
        
        # 添加到分组
        if group not in self.groups:
            self.groups[group] = []
        if name not in self.groups[group]:
            self.groups[group].append(name)
        
        self.logger.info(f"模板注册成功: {name} -> {path}")
        return True
    
    def unregister_template(self, name: str) -> bool:
        """
        取消注册模板
        
        Args:
            name: 模板名称
            
        Returns:
            是否成功
        """
        if name not in self.templates:
            return False
        
        template_info = self.templates[name]
        group = template_info.group
        
        # 从注册表移除
        del self.templates[name]
        
        # 从分组移除
        if group in self.groups and name in self.groups[group]:
            self.groups[group].remove(name)
            
            # 如果分组为空，删除分组
            if not self.groups[group]:
                del self.groups[group]
        
        self.logger.info(f"模板取消注册: {name}")
        return True
    
    def get_template_info(self, name: str) -> Optional[TemplateInfo]:
        """获取模板信息"""
        return self.templates.get(name)
    
    def list_templates(self, group: Optional[str] = None) -> List[TemplateInfo]:
        """
        列出模板
        
        Args:
            group: 指定分组，None表示所有分组
            
        Returns:
            模板信息列表
        """
        if group is None:
            return list(self.templates.values())
        
        if group not in self.groups:
            return []
        
        return [self.templates[name] for name in self.groups[group] 
                if name in self.templates]
    
    def list_groups(self) -> List[str]:
        """列出所有分组"""
        return list(self.groups.keys())
    
    def search_templates(self, keyword: str, 
                        group: Optional[str] = None,
                        search_tags: bool = True,
                        search_description: bool = True) -> List[TemplateInfo]:
        """
        搜索模板
        
        Args:
            keyword: 搜索关键词
            group: 限定分组
            search_tags: 是否搜索标签
            search_description: 是否搜索描述
            
        Returns:
            匹配的模板列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        templates_to_search = self.list_templates(group)
        
        for template in templates_to_search:
            # 搜索名称
            if keyword_lower in template.name.lower():
                results.append(template)
                continue
            
            # 搜索描述
            if search_description and keyword_lower in template.description.lower():
                results.append(template)
                continue
            
            # 搜索标签
            if search_tags:
                for tag in template.tags:
                    if keyword_lower in tag.lower():
                        results.append(template)
                        break
        
        return results
    
    def get_templates_by_tag(self, tag: str) -> List[TemplateInfo]:
        """根据标签获取模板"""
        tag_lower = tag.lower()
        return [template for template in self.templates.values()
                if any(t.lower() == tag_lower for t in template.tags)]
    
    def validate_templates(self) -> Dict[str, List[str]]:
        """
        验证所有模板文件
        
        Returns:
            验证结果 {"valid": [...], "missing": [...], "invalid": [...]}
        """
        result = {"valid": [], "missing": [], "invalid": []}
        
        for name, template in self.templates.items():
            path = Path(template.path)
            
            if not path.exists():
                result["missing"].append(name)
            elif path.suffix.lower() not in self.supported_formats:
                result["invalid"].append(name)
            else:
                result["valid"].append(name)
        
        self.logger.info(f"模板验证完成 - 有效: {len(result['valid'])}, "
                        f"缺失: {len(result['missing'])}, "
                        f"无效: {len(result['invalid'])}")
        
        return result
    
    def save_registry(self) -> bool:
        """保存模板注册表到文件"""
        try:
            registry_data = {
                "templates": {name: asdict(info) for name, info in self.templates.items()},
                "groups": self.groups,
                "version": "1.0"
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"模板注册表已保存: {self.registry_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存模板注册表失败: {e}")
            return False
    
    def load_registry(self) -> bool:
        """从文件加载模板注册表"""
        if not self.registry_file.exists():
            return False
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            # 加载模板信息
            templates_data = registry_data.get("templates", {})
            for name, template_dict in templates_data.items():
                # 只有当模板文件存在时才加载
                if Path(template_dict["path"]).exists():
                    self.templates[name] = TemplateInfo(**template_dict)
            
            # 加载分组信息
            self.groups = registry_data.get("groups", {})
            
            # 过滤掉不存在的模板
            for group_name, template_names in self.groups.items():
                self.groups[group_name] = [name for name in template_names 
                                         if name in self.templates]
            
            self.logger.debug(f"模板注册表已加载: {len(self.templates)} 个模板")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模板注册表失败: {e}")
            return False
    
    def create_group(self, group_name: str, template_names: List[str] = None) -> bool:
        """
        创建模板分组
        
        Args:
            group_name: 分组名称
            template_names: 模板名称列表
            
        Returns:
            是否创建成功
        """
        if group_name in self.groups:
            self.logger.warning(f"分组已存在: {group_name}")
            return False
        
        self.groups[group_name] = template_names or []
        
        # 更新模板的分组信息
        if template_names:
            for name in template_names:
                if name in self.templates:
                    self.templates[name].group = group_name
        
        self.logger.info(f"分组创建成功: {group_name}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        stats = {
            "total_templates": len(self.templates),
            "total_groups": len(self.groups),
            "groups_stats": {},
            "format_stats": {},
            "size_stats": {"total_size": 0, "avg_size": 0}
        }
        
        # 分组统计
        for group, templates in self.groups.items():
            stats["groups_stats"][group] = len(templates)
        
        # 格式统计
        total_size = 0
        for template in self.templates.values():
            try:
                file_path = Path(template.path)
                if file_path.exists():
                    size = file_path.stat().st_size
                    total_size += size
                    
                    ext = file_path.suffix.lower()
                    stats["format_stats"][ext] = stats["format_stats"].get(ext, 0) + 1
            except:
                pass
        
        stats["size_stats"]["total_size"] = total_size
        stats["size_stats"]["avg_size"] = total_size / max(len(self.templates), 1)
        
        return stats


# 全局模板管理器实例
template_manager = TemplateManager()


def get_template_path(template_name: str, group: Optional[str] = None) -> Optional[str]:
    """便捷函数：获取模板路径"""
    return template_manager.get_template_path(template_name, group)


def register_template(name: str, path: str, group: str = 'default', **kwargs) -> bool:
    """便捷函数：注册模板"""
    return template_manager.register_template(name, path, group, **kwargs)


def list_templates(group: Optional[str] = None) -> List[TemplateInfo]:
    """便捷函数：列出模板"""
    return template_manager.list_templates(group)


def search_templates(keyword: str, **kwargs) -> List[TemplateInfo]:
    """便捷函数：搜索模板"""
    return template_manager.search_templates(keyword, **kwargs)