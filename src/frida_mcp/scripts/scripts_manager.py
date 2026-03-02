import frida

import os
from typing import Optional, Dict, Any, Deque, List

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


class ScriptManager:
    def __init__(self):
        self.open_script:str = init_script()

    def init_script(self):
        self.open_script:str = init_script()

    