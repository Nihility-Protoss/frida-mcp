import frida
from typing import Dict, Any
from collections import deque

from .inject import BaseInjector

class AndroidInjector(BaseInjector):
    """
    Android平台专用注入器实现
    符合BaseInjector抽象方法签名
    """
    
    def __init__(self, device: frida.core.Device, messages_buffer: deque):
        super().__init__(device, messages_buffer)
    
    async def attach(self, target: str) -> Dict[str, Any]:
        """
        附加到Android进程
        
        Args:
            target: 目标进程（PID或包名）
            
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
                package_name = target
                app_name = target
            else:
                applications = device.enumerate_applications()
                target_app = None
                
                for app in applications:
                    if app.identifier == target and app.pid and app.pid > 0:
                        target_app = app
                        break
                
                if not target_app:
                    return {'error': f'Unable to find running app: {target}', 'data': None}
                
                pid = target_app.pid
                package_name = app.identifier
                app_name = target_app.name
            
            # 附加到进程
            self.session = device.attach(pid)
            self._bind_session_events(self.session)
            
            self.current_target = package_name
            self.current_pid = pid
            
            return {
                'error': None,
                'data': {
                    'pid': pid,
                    'package': package_name,
                    'name': app_name,
                    'message': 'Successfully attached to Android process'
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'data': None}
    
    async def spawn(self, target: str) -> Dict[str, Any]:
        """
        启动Android应用
        
        Args:
            target: 应用包名
            
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
            
            # 启动应用
            pid = device.spawn(target)
            self.session = device.attach(pid)
            self._bind_session_events(self.session)
            
            self.current_target = target
            self.current_pid = pid
            
            return {
                'error': None,
                'data': {
                    'pid': pid,
                    'package': target,
                    'message': 'Successfully spawned Android app (paused)'
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'data': None}
