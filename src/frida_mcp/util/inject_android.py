import frida
from typing import Dict, Any, Optional
from src.frida_mcp.util.inject import BaseInjector

class AndroidInjector(BaseInjector):
    """
    Concrete implementation of BaseInjector for Android devices.
    """
    async def attach(self, target: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Attach to a process on Android and inject script."""
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
                applications = self.device.enumerate_applications()
                target_app = None
                
                for app in applications:
                    if app.identifier == target and app.pid and app.pid > 0:
                        target_app = app
                        break
                
                if not target_app:
                    return {
                        "status": "error",
                        "message": f"Unable to find running app: {target}"
                    }
                
                pid = target_app.pid
                app_name = target_app.name
            
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

    async def spawn(self, package_name: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Spawn an app on Android and inject script before resuming."""
        # Cleanup old session
        if self.session:
            try:
                self.session.detach()
            except:
                pass
            self.session = None

        try:
            # Spawn
            pid = self.device.spawn(package_name)
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
                "package": package_name,
                "script_loaded": script_loaded,
                "message": "App spawned successfully."
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
