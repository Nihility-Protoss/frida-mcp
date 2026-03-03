import frida
import os
import re
from typing import Optional, Dict, Any, Deque, List, Union
from pathlib import Path

def init_script() -> str:
    return f"""
    // Smart object to string function (prefers Gson)
    function safeStringify(obj) {{
        if (obj === null) return 'null';
        if (obj === undefined) return 'undefined';

        // Basic types
        if (typeof obj === 'string') return obj;
        if (typeof obj === 'number' || typeof obj === 'boolean') return String(obj);

        // Objects
        try {{
            var Gson = Java.use('com.google.gson.Gson');
            var gson = Gson.$new();
            return gson.toJson(obj);
        }} catch (gsonError) {{
            try {{
                return obj.toString();
            }} catch (toStringError) {{
                try {{
                    return '[' + (obj.$className || 'Unknown') + ' Object]';
                }} catch (classError) {{
                    return '[Unparseable Object]';
                }}
            }}
        }}
    }}

    // Redirect console.log to send()
    console.log = function() {{
        var message = Array.prototype.slice.call(arguments).map(function(arg) {{
            return safeStringify(arg);
        }}).join(' ');
        send({{'type': 'log', 'message': message}});
    }};

    // User script
    """


class JSFileLoader:
    """JS文件加载器，用于读取和管理JS文件"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化JS文件加载器
        
        Args:
            scripts_dir: JS文件目录路径，如果为None则使用默认路径
        """
        if scripts_dir:
            self.scripts_dir = Path(scripts_dir)
        else:
            # 默认使用当前文件所在目录的js子目录
            self.scripts_dir = Path(__file__).parent / "js"
        
        # 确保目录存在
        self.scripts_dir.mkdir(exist_ok=True)
    
    def load_js_file(self, filename: str) -> Dict[str, Any]:
        """加载单个JS文件
        
        Args:
            filename: JS文件名（可包含子目录）
            
        Returns:
            dict: {'error': str, 'data': str}
                error: 错误信息，成功时为None
                data: JS文件内容
        """
        try:
            file_path = self.scripts_dir / filename
            if not file_path.exists():
                return {'error': f'JS file not found: {file_path}', 'data': None}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {'error': None, 'data': content}
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    def load_js_files(self, pattern: str = "*.js") -> Dict[str, Any]:
        """批量加载JS文件
        
        Args:
            pattern: 文件匹配模式，默认为*.js
            
        Returns:
            dict: {'error': str, 'data': Dict[str, str]}
                error: 错误信息，成功时为None
                data: 文件名到内容的字典
        """
        try:
            files_content = {}
            for js_file in self.scripts_dir.rglob(pattern):
                relative_path = js_file.relative_to(self.scripts_dir)
                result = self.load_js_file(str(relative_path))
                if result['error']:
                    return {'error': result['error'], 'data': {}}
                files_content[str(relative_path)] = result['data']
            return {'error': None, 'data': files_content}
        except Exception as e:
            return {'error': str(e), 'data': {}}
    
    def get_available_files(self, pattern: str = "*.js") -> Dict[str, Any]:
        """获取可用的JS文件列表
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            dict: {'error': str, 'data': List[str]}
                error: 错误信息，成功时为None
                data: 相对路径的文件名列表
        """
        try:
            files = [str(f.relative_to(self.scripts_dir)) 
                    for f in self.scripts_dir.rglob(pattern)]
            return {'error': None, 'data': files}
        except Exception as e:
            return {'error': str(e), 'data': []}


class StringReplacer:
    """字符串替换器，用于处理JS模板中的变量替换"""
    
    def __init__(self):
        self.template_pattern = re.compile(r'\{\{(\w+)\}\}')
    
    def replace_placeholders(self, template: str, **kwargs) -> str:
        """替换模板中的占位符
        
        Args:
            template: 包含占位符的模板字符串
            **kwargs: 替换字典
            
        Returns:
            替换后的字符串
        """
        def replacer(match):
            key = match.group(1)
            return str(kwargs.get(key, match.group(0)))
        
        return self.template_pattern.sub(replacer, template)
    
    def replace_with_dict(self, template: str, replacements: Dict[str, Any]) -> str:
        """使用字典进行批量替换
        
        Args:
            template: 模板字符串
            replacements: 替换字典
            
        Returns:
            替换后的字符串
        """
        return self.replace_placeholders(template, **replacements)


class ScriptBuilder:
    """脚本构建器，用于构建最终的Frida脚本"""
    
    def __init__(self, base_script: str = None):
        """初始化脚本构建器
        
        Args:
            base_script: 基础脚本，如果为None则使用默认的init_script
        """
        self.base_script = base_script or init_script()
        self.sections = []
    
    def add_section(self, name: str, content: str) -> 'ScriptBuilder':
        """添加脚本片段
        
        Args:
            name: 片段名称（用于注释）
            content: 脚本内容
            
        Returns:
            self，支持链式调用
        """
        self.sections.append(f"\n// === {name} ===\n{content}")
        return self
    
    def add_js_file(self, filename: str, content: str) -> 'ScriptBuilder':
        """添加JS文件内容
        
        Args:
            filename: 文件名（用于注释）
            content: JS内容
            
        Returns:
            self，支持链式调用
        """
        return self.add_section(f"Loaded from {filename}", content)
    
    def build(self) -> str:
        """构建最终脚本
        
        Returns:
            完整的Frida脚本
        """
        return self.base_script + "".join(self.sections)


class ScriptManager:
    """脚本管理器，统一管理Frida脚本的加载和构建"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化脚本管理器
        
        Args:
            scripts_dir: JS文件目录路径
        """
        self.file_loader = JSFileLoader(scripts_dir)
        self.replacer = StringReplacer()
        self.builder = ScriptBuilder()
        self.open_script: str = self.builder.build()
    
    
    
    def load_script_from_file(self, filename: str, **replacements) -> Dict[str, Any]:
        """从文件加载并构建脚本
        
        Args:
            filename: JS文件名
            **replacements: 模板替换参数
            
        Returns:
            dict: {'error': str, 'data': str}
                error: 错误信息，成功时为None
                data: 构建完成的脚本
        """
        try:
            result = self.file_loader.load_js_file(filename)
            if result['error']:
                return result
            
            content = result['data']
            
            # 如果有替换参数，进行替换
            if replacements:
                content = self.replacer.replace_with_dict(content, replacements)
            
            # 重新构建脚本
            self.builder = ScriptBuilder()
            self.builder.add_js_file(filename, content)
            self.open_script = self.builder.build()
            
            return {'error': None, 'data': self.open_script}
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    def load_multiple_scripts(self, filenames: List[str], **replacements) -> Dict[str, Any]:
        """加载多个脚本文件
        
        Args:
            filenames: 文件名列表
            **replacements: 模板替换参数
            
        Returns:
            dict: {'error': str, 'data': str}
                error: 错误信息，成功时为None
                data: 构建完成的脚本
        """
        try:
            self.builder = ScriptBuilder()
            
            for filename in filenames:
                result = self.file_loader.load_js_file(filename)
                if result['error']:
                    return result
                
                content = result['data']
                if replacements:
                    content = self.replacer.replace_with_dict(content, replacements)
                self.builder.add_js_file(filename, content)
            
            self.open_script = self.builder.build()
            return {'error': None, 'data': self.open_script}
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    def add_custom_section(self, name: str, content: str, **replacements) -> Dict[str, Any]:
        """添加自定义脚本片段
        
        Args:
            name: 片段名称
            content: 脚本内容
            **replacements: 模板替换参数
            
        Returns:
            dict: {'error': str, 'data': str}
                error: 错误信息，成功时为None
                data: 更新后的脚本
        """
        try:
            if replacements:
                content = self.replacer.replace_with_dict(content, replacements)
            
            self.builder.add_section(name, content)
            self.open_script = self.builder.build()
            return {'error': None, 'data': self.open_script}
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    def reset_script(self) -> Dict[str, Any]:
        """重置为初始脚本
        
        Returns:
            dict: {'error': str, 'data': str}
                error: 错误信息，成功时为None
                data: 重置后的脚本
        """
        try:
            self.builder = ScriptBuilder()
            self.open_script = self.builder.build()
            return {'error': None, 'data': self.open_script}
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    def get_available_scripts(self) -> Dict[str, Any]:
        """获取可用的脚本文件列表
        
        Returns:
            dict: {'error': str, 'data': List[str]}
                error: 错误信息，成功时为None
                data: 可用的JS文件名列表
        """
        try:
            files = self.file_loader.get_available_files()
            return {'error': None, 'data': files}
        except Exception as e:
            return {'error': str(e), 'data': []}
    
    def init_script(self) -> Dict[str, Any]:
        """初始化脚本（保持向后兼容）"""
        return self.reset_script()