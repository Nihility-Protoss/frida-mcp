from typing import Dict, Any

import frida

from scripts.windows_script_manager import WindowsScriptManager
from .inject import BaseInjector
from .message_class import MessageLog


class WindowsInjector(BaseInjector):
    """
    Windows平台专用注入器实现
    符合BaseInjector抽象方法签名
    """

    def __init__(self, device: frida.core.Device, messages_buffer: MessageLog):
        super().__init__(device, messages_buffer)
        self.script_manager = WindowsScriptManager()

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

            self.current_target = process_name
            self.current_pid = pid
            self.needs_resume = False

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

    async def spawn(self, target: str, args: str = "") -> Dict[str, Any]:
        """
        启动Windows程序
        
        Args:
            target: 程序名称或路径
            args: 启动参数（可选），如 "--arg1 value1 --arg2"
            
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

            # 构建完整命令（用于显示）
            full_command = target

            # 构建argv参数列表
            if args and args.strip():
                import shlex
                argv = shlex.split(args.strip())
                full_command = f"{target} {args.strip()}"
            else:
                argv = []

            # 启动程序（Windows 也使用 argv 参数）
            pid = device.spawn([target], argv=argv if argv else None)
            self.session = device.attach(pid)

            self.current_target = full_command
            self.current_pid = pid
            self.needs_resume = True

            return {
                'error': None,
                'data': {
                    'pid': pid,
                    'program': full_command,
                    'message': 'Successfully spawned Windows program (paused)'
                }
            }

        except Exception as e:
            return {'error': str(e), 'data': None}
