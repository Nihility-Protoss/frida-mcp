"""
修正的BaseInjector类，符合指定的抽象方法签名
"""

import frida
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from collections import deque

class BaseInjector(ABC):
    """
    修正的BaseInjector类，符合指定的抽象方法签名
    device信息在初始化时传入，messages_buffer必须传入
    """
    
    def __init__(self, device: frida.core.Device, messages_buffer: deque):
        """
        初始化注入器
        
        Args:
            device: Frida设备实例（必须传入）
            messages_buffer: 消息缓冲区（必须传入）
        """
        self.device = device
        self.messages_buffer = messages_buffer
        self.session: Optional[frida.core.Session] = None
        self.current_target: Optional[str] = None
        self.current_pid: Optional[int] = None
    
    def __str__(self):
        return f"{self.__class__.__name__}-{self.current_target}-{self.current_pid}"
    
    def _log(self, text: str) -> None:
        """记录日志消息"""
        message = f"[{self.__class__.__name__}] {text}"
        self.messages_buffer.append(message)
        print(message)
    
    def _bind_session_events(self, session: frida.core.Session) -> None:
        """绑定session事件"""
        def on_detached(reason):
            self._log(f"Session detached: {reason}")
            self.session = None
        
        def on_message(message, data):
            if message['type'] == 'send':
                self._log(f"Script message: {message['payload']}")
            elif message['type'] == 'error':
                self._log(f"Script error: {message['description']}")
        
        session.on('detached', on_detached)
        session.on('message', on_message)
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.session is not None
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        获取当前会话信息

        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为 None
                data: 会话信息
        """
        if not self.session:
            return {
                'error': "No active session. Please re call attach or spawn.",
                'data': None
            }

        try:
            return {
                'error': None,
                'data': {
                    'target': self.current_target,
                    'pid': self.current_pid
                }
            }
        except Exception as e:
            return {'error': str(e), 'data': None}

    def inject_script(self, script_manager, script_name: str = "default") -> Dict[str, Any]:
        """
        使用ScriptManager将脚本注入到当前session

        Args:
            script_manager: ScriptManager实例
            script_name: 脚本名称标识符

        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 注入结果信息
        """
        if not self.session:
            return {'error': 'No active session. Please attach or spawn first.', 'data': None}

        try:
            # 获取当前脚本内容
            script_content = script_manager.open_script
            if not script_content:
                return {'error': 'No script content available', 'data': None}

            # 创建并加载脚本
            script = self.session.create_script(script_content)
            script.on('message', lambda message, data: self._handle_script_message(script_name, message, data))
            script.load()

            return {
                'error': None,
                'data': {
                    'script_name': script_name,
                    'script_content_length': len(script_content)
                }
            }

        except Exception as e:
            return {'error': str(e), 'data': None}

    def _handle_script_message(self, script_name: str, message: Dict[str, Any], data: bytes) -> None:
        """处理脚本消息"""
        if message['type'] == 'send':
            self._log(f"[{script_name}] {message['payload']}")
        elif message['type'] == 'error':
            self._log(f"[{script_name}] ERROR: {message['description']}")
    
    @abstractmethod
    async def attach(self, target: str) -> Dict[str, Any]:
        """
        附加到进程
        
        Args:
            target: 目标进程（PID或名称）
            
        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 附加结果信息
        """
        pass
    
    @abstractmethod
    async def spawn(self, target: str) -> Dict[str, Any]:
        """
        启动进程
        
        Args:
            target: 目标进程（包名或程序名）
            
        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 启动结果信息
        """
        pass
    
    def detach(self) -> Dict[str, Any]:
        """
        断开连接
        
        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 断开结果信息
        """
        try:
            if self.session:
                self.session.detach()
                self.session = None
                self.current_target = None
                self.current_pid = None
                
                return {'error': None, 'data': {'message': 'Successfully detached'}}
            else:
                return {'error': 'No active session to detach', 'data': None}
                
        except Exception as e:
            return {'error': str(e), 'data': None}