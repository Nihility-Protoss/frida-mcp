// Windows注册表监控脚本
var registryPath = "{{registry_path}}";

console.log("[+] Monitoring registry: " + registryPath);

// Hook RegOpenKeyExW
var RegOpenKeyExW = Module.getExportByName('advapi32.dll', 'RegOpenKeyExW');
Interceptor.attach(RegOpenKeyExW, {
    onEnter: function(args) {
        var hKey = args[0];
        var lpSubKey = args[1];
        var ulOptions = args[2];
        var samDesired = args[3];
        var phkResult = args[4];
        
        var subKey = Memory.readUtf16String(lpSubKey);
        
        if (subKey.includes(registryPath)) {
            console.log("[+] RegOpenKeyExW called for: " + subKey);
            console.log("[+] hKey: 0x" + hKey.toString(16));
            console.log("[+] samDesired: 0x" + samDesired.toString(16));
        }
    }
});

// Hook RegSetValueExW
var RegSetValueExW = Module.getExportByName('advapi32.dll', 'RegSetValueExW');
Interceptor.attach(RegSetValueExW, {
    onEnter: function(args) {
        var hKey = args[0];
        var lpValueName = args[1];
        var Reserved = args[2];
        var dwType = args[3];
        var lpData = args[4];
        var cbData = args[5];
        
        var valueName = Memory.readUtf16String(lpValueName);
        var data = Memory.readUtf16String(lpData);
        
        console.log("[+] RegSetValueExW called");
        console.log("[+] Value name: " + valueName);
        console.log("[+] Data: " + data);
        console.log("[+] Data type: 0x" + dwType.toString(16));
    }
});