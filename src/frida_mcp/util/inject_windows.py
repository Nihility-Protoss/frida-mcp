import frida
from typing import Dict, Any
from collections import deque

from .inject import BaseInjector

class WindowsInjector(BaseInjector):
    """
    Windows平台专用注入器实现
    符合BaseInjector抽象方法签名
    """
    
    def __init__(self, device: frida.core.Device, messages_buffer: deque):
        super().__init__(device, messages_buffer)
    
    async def attach(self, target: str) -> Dict[str, Any]:
        """
        附加到Windows进程
        
        Args:
            target: 目标进程（PID或进程名）
            
        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 附加结果信息
        """
        # 清理旧会话
        detach_result = self.detach()
        if detach_result['error']:
            self._log(f"Warning: Failed to detach old session: {detach_result['error']}")
        
        target = target.strip()
        
        try:
            # 使用初始化时的device
            device = self.device
            
            # 确定PID
            if target.isdigit():
                pid = int(target)
                process_name = target
            else:
                # Windows使用enumerate_processes
                processes = device.enumerate_processes()
                target_process = None
                
                for proc in processes:
                    if proc.name.lower() == target.lower():
                        target_process = proc
                        break
                
                if not target_process:
                    return {'error': f'Unable to find running process: {target}', 'data': None}
                
                pid = target_process.pid
                process_name = target_process.name
            
            # 附加到进程
            self.session = device.attach(pid)
            self._bind_session_events(self.session)
            
            self.current_target = process_name
            self.current_pid = pid
            
            return {
                'error': None,
                'data': {
                    'pid': pid,
                    'process': process_name,
                    'message': 'Successfully attached to Windows process'
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    async def spawn(self, target: str) -> Dict[str, Any]:
        """
        启动Windows程序
        
        Args:
            target: 程序名称或路径
            
        Returns:
            dict: {'error': str, 'data': dict}
                error: 错误信息，成功时为None
                data: 启动结果信息
        """
        # 清理旧会话
        detach_result = self.detach()
        if detach_result['error']:
            self._log(f"Warning: Failed to detach old session: {detach_result['error']}")
        
        try:
            # 使用初始化时的device
            device = self.device
            
            # 启动程序
            pid = device.spawn([target])  # Frida spawn expects a list of arguments
            self.session = device.attach(pid)
            self._bind_session_events(self.session)
            
            self.current_target = target
            self.current_pid = pid
            
            return {
                'error': None,
                'data': {
                    'pid': pid,
                    'program': target,
                    'message': 'Successfully spawned Windows program (paused)'
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'data': None}
