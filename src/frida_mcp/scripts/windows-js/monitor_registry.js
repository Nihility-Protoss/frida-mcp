// Windows注册表监控脚本
function monitorRegistry() {
    const registryPath = "{{registry_path}}";
    console.log(`[+] Monitoring registry: ${registryPath}`);

    // Hook RegOpenKeyExW
    const RegOpenKeyExW = Module.getExportByName('advapi32.dll', 'RegOpenKeyExW');
    Interceptor.attach(RegOpenKeyExW, {
        onEnter: function(args) {
            const hKey = args[0];
            const lpSubKey = args[1];
            const ulOptions = args[2];
            const samDesired = args[3];
            const phkResult = args[4];
            
            const subKey = Memory.readUtf16String(lpSubKey);
            
            if (subKey.includes(registryPath)) {
                console.log(`[+] RegOpenKeyExW called for: ${subKey}`);
                console.log(`[+] hKey: 0x${hKey.toString(16)}`);
                console.log(`[+] samDesired: 0x${samDesired.toString(16)}`);
            }
        }
    });

    // Hook RegSetValueExW
    const RegSetValueExW = Module.getExportByName('advapi32.dll', 'RegSetValueExW');
    Interceptor.attach(RegSetValueExW, {
        onEnter: function(args) {
            const hKey = args[0];
            const lpValueName = args[1];
            const Reserved = args[2];
            const dwType = args[3];
            const lpData = args[4];
            const cbData = args[5];
            
            const valueName = Memory.readUtf16String(lpValueName);
            const data = Memory.readUtf16String(lpData);
            
            console.log("[+] RegSetValueExW called");
            console.log(`[+] Value name: ${valueName}`);
            console.log(`[+] Data: ${data}`);
            console.log(`[+] Data type: 0x${dwType.toString(16)}`);
        }
    });
}

// 执行监控
monitorRegistry();