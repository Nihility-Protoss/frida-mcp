import frida
from typing import Dict, Any, Optional
from src.frida_mcp.util.inject import BaseInjector

class WindowsInjector(BaseInjector):
    """
    Concrete implementation of BaseInjector for Windows devices.
    """
    async def attach(self, target: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Attach to a process on Windows and inject script."""
        # Cleanup old session
        if self.session:
            try:
                self.session.detach()
            except:
                pass
            self.session = None

        target = target.strip()
        
        try:
            # Determine PID
            if target.isdigit():
                pid = int(target)
                app_name = target
            else:
                # On Windows, enumerate_processes is more common than enumerate_applications
                processes = self.device.enumerate_processes()
                target_process = None
                
                for proc in processes:
                    if proc.name.lower() == target.lower():
                        target_process = proc
                        break
                
                if not target_process:
                    return {
                        "status": "error",
                        "message": f"Unable to find running process: {target}"
                    }
                
                pid = target_process.pid
                app_name = target_process.name
            
            # Attach
            self.session = self.device.attach(pid)
            self._bind_session_events(self.session)
            
            # Inject script
            script_loaded = False
            if script_content:
                try:
                    script_loaded = await self._load_script(self.session, script_content, output_file=output_file)
                except Exception as e:
                    self._log(f"script load error: {e}")
                    return {"status": "error", "message": str(e)}
            
            return {
                "status": "success",
                "pid": pid,
                "target": target,
                "name": app_name,
                "script_loaded": script_loaded,
                "message": "Attached successfully."
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def spawn(self, program_name: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Spawn a program on Windows and inject script before resuming."""
        # Cleanup old session
        if self.session:
            try:
                self.session.detach()
            except:
                pass
            self.session = None

        try:
            # Spawn
            pid = self.device.spawn([program_name]) # Frida spawn expects a list of arguments
            self.session = self.device.attach(pid)
            self._bind_session_events(self.session)
            
            # Inject script
            script_loaded = False
            if script_content:
                try:
                    script_loaded = await self._load_script(self.session, script_content, init_delay=0.1, output_file=output_file)
                except Exception as e:
                    self._log(f"script load error: {e}")
                    return {"status": "error", "message": str(e)}
            
            # Resume
            self.device.resume(pid)
            
            return {
                "status": "success",
                "pid": pid,
                "program": program_name,
                "script_loaded": script_loaded,
                "message": "Program spawned successfully."
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
