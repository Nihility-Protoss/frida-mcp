"""
修正的BaseInjector类，符合指定的抽象方法签名
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Union

import frida

from scripts.android_script_manager import AndroidScriptManager
from scripts.scripts_manager import ScriptManager
from scripts.windows_script_manager import WindowsScriptManager
from .message_class import MessageLog


class BaseInjector(ABC):
    """
    修正的BaseInjector类，符合指定的抽象方法签名
    device信息在初始化时传入，messages_buffer必须传入
    """

    def __init__(self, device: frida.core.Device, messages_buffer: MessageLog):
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
        self.script_manager: Optional[
            Union[ScriptManager | AndroidScriptManager | WindowsScriptManager]
        ] = None
        self.needs_resume: bool = False
        self.running_script: Optional[frida.core.Script] = None

    def __str__(self):
        return f"{self.__class__.__name__}-{self.current_target}-{self.current_pid}"

    def _log(self, text: str) -> None:
        """记录日志消息"""
        message = f"[{self.__class__.__name__}] {text}"
        self.messages_buffer.append(message)
        # print(message)

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

    def get_script_manager(self) -> ScriptManager:
        return self.script_manager

    def inject_script(self, script_manager: ScriptManager = None) -> Dict[str, Any]:
        """
        使用 self.ScriptManager 将脚本注入到当前session

        Args:
            script_manager: 用户输入的单独执行的script，不影响class中的执行流

        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 注入结果信息
        """
        if not self.session:
            return {
                'error': 'No active session. Please attach or spawn first.',
                'data': None
            }

        script_manager = self.script_manager if script_manager is None else script_manager

        try:
            # 获取当前脚本内容
            script_content = str(script_manager)
            if not script_content:
                return {
                    'error': 'No script content available',
                    'data': None
                }

            script_name = f"{len(script_manager.name)}: {script_manager.name[-1]}"

            if self.running_script is not None:
                try:
                    self.running_script.unload()
                except Exception as e:
                    # 可能是原session已经detach，导致unload失败
                    print(str(e))
                    self.running_script = None

            # 创建并加载脚本
            script = self.session.create_script(script_content)
            script.on('message', lambda message, data: self._handle_script_message(script_name, message, data))
            script.load()
            self.running_script = script

            if self.needs_resume:
                self.device.resume(self.current_pid)
                self.needs_resume = False

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
            payload = message['payload']
            
            # 处理内存 dump 消息
            if isinstance(payload, dict):
                msg_type = payload.get('type')
                if msg_type == 'memory_dump':
                    self._handle_memory_dump(payload, data)
                    return
                elif msg_type == 'executable_memory_alert':
                    self._handle_executable_alert(payload)
                    return
            
            # 普通日志消息
            self._log(f"[{script_name}] {payload}")
            
        elif message['type'] == 'error':
            self._log(f"[{script_name}] ERROR: {message['stack']}")

    def _handle_executable_alert(self, payload: Dict[str, Any]) -> None:
        """
        处理可执行内存告警
        注意：详细日志由JS端统一发送，此函数仅做必要的本地处理
        """
        try:
            action = payload.get('action', 'unknown')
            extraInfo = payload.get('extraInfo', {})
            
            # 只在关键动作时输出简洁确认，避免与JS端日志重复
            if action == 'dump_on_first_execute':
                caller = extraInfo.get('caller', 'unknown')
                self._log(f"[ALERT] First execution at {caller}")
            elif action == 'transition':
                prev = extraInfo.get('previousProtect', 'unknown')
                new = extraInfo.get('newProtect', 'unknown')
                self._log(f"[ALERT] {prev} -> {new}")
            # immediate_dump 和 monitor_first_execute 不输出（JS端已发送详细日志）
        except Exception as e:
            self._log(f"[ALERT ERROR] {str(e)}")

    def _handle_memory_dump(self, payload: Dict[str, Any], data: bytes) -> None:
        """
        保存内存 dump 到文件
        注意：此函数只负责文件保存，不输出日志（日志由JS端统一发送）
        
        Args:
            payload: 消息payload，包含filename, address, size等信息
            data: 二进制内存数据（由JS端读取并发送）
        """
        from datetime import datetime
        
        try:
            filename = payload.get('filename', f"dump_{datetime.now().timestamp()}.bin")
            pid = payload.get('pid', self.current_pid or 'unknown')
            
            # 创建dump目录
            dump_dir = Path("memory_dumps")
            dump_dir.mkdir(exist_ok=True)
            
            # 添加PID子目录
            pid_dir = dump_dir / str(pid)
            pid_dir.mkdir(exist_ok=True)
            
            filepath = pid_dir / filename
            
            if data:
                with open(filepath, 'wb') as f:
                    f.write(data)
                # 发送成功确认消息（仅包含文件路径，避免重复信息）
                self._log(f"[DUMP SAVED] {filepath}")
            else:
                self._log(f"[DUMP ERROR] No data received for {filename}")
                
        except Exception as e:
            self._log(f"[DUMP ERROR] Failed to save: {str(e)}")

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
    async def spawn(self, target: str, args: str = "") -> Dict[str, Any]:
        """
        启动进程
        
        Args:
            target: 目标进程（包名或程序路径）
            args: 启动参数（可选），如 "--arg1 value1 --arg2"
            
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
