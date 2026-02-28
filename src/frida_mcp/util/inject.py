from abc import ABC, abstractmethod
import frida
import asyncio
import os
from typing import Optional, Dict, Any, Deque, List

class BaseInjector(ABC):
    """
    Abstract base class for handling Frida injection.
    Provides common functionalities like script wrapping, message collection,
    and script loading, while deferring device-specific logic to subclasses.
    """
    def __init__(self, device: frida.core.Device, messages_buffer: Deque[str], frida_log_callback):
        self.device = device
        self.messages_buffer = messages_buffer
        self.frida_log = frida_log_callback
        self.active_scripts: List[frida.core.Script] = []
        self.session: Optional[frida.core.Session] = None

    def _log(self, text: str) -> None:
        if self.frida_log:
            self.frida_log(text)

    def _bind_session_events(self, sess: frida.core.Session) -> None:
        """Bind session events to capture detach reasons."""
        try:
            def on_detached(reason):
                self._log(f"session detached: {reason}")
            sess.on('detached', on_detached)
        except Exception as e:
            self._log(f"bind detached failed: {e}")

    @staticmethod
    def wrap_script(user_script: str) -> str:
        """Wrap user script with logging and helper functions."""
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
        {user_script}
        """

    def _create_message_collector(self, output_file: Optional[str] = None):
        """Creates a message handler that collects Frida script output."""
        messages = []
        
        if output_file and os.path.exists(output_file):
            try:
                open(output_file, 'w', encoding='utf-8').close()
            except Exception:
                pass

        def on_message(message, data):
            if message.get('type') == 'send':
                payload = message.get('payload', {})
                if isinstance(payload, dict) and payload.get('type') == 'log':
                    text = payload.get('message', str(payload))
                else:
                    text = str(payload)
            elif message.get('type') == 'error':
                text = f"[Error] {message.get('stack', message.get('description', str(message)))}"
            else:
                if 'payload' in message:
                    text = str(message['payload'])
                else:
                    text = str(message)

            messages.append(text)
            if self.messages_buffer is not None:
                self.messages_buffer.append(text)

            if output_file:
                try:
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(f"{text}\n")
                except Exception:
                    pass

        return on_message, messages

    async def _load_script(self, session: frida.core.Session, script_content: str, init_delay: float = 0.0, output_file: Optional[str] = None) -> bool:
        """Load script and wire message collector."""
        if not script_content:
            return False
        
        wrapped_script = BaseInjector.wrap_script(script_content)
        script = session.create_script(wrapped_script)
        
        # Clear buffer
        try:
            while len(self.messages_buffer) > 0:
                self.messages_buffer.pop()
        except Exception:
            pass
            
        handler, _ = self._create_message_collector(output_file)
        script.on('message', handler)
        script.load()
        
        # Keep reference
        self.active_scripts.append(script)
        
        if init_delay > 0:
            await asyncio.sleep(init_delay)
        return True

    @abstractmethod
    async def attach(self, target: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Attach to a process and inject script."""
        pass

    @abstractmethod
    async def spawn(self, package_name: str, script_content: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Spawn an app and inject script before resuming."""
        pass
