// Windows注册表监控脚本 - 监控特定注册表路径

/**
 * 监控RegOpenKeyExW API的使用情况
 * 对特定注册表路径有特征输出
 */
function monitorRegistry_RegOpenKeyExW() {
    console.log("[+] Setting up RegOpenKeyExW monitor...");

    const advapi32 = Process.getModuleByName('advapi32.dll');
    if (!advapi32) {
        console.log("[-] advapi32.dll module not found");
        return;
    }

    try {
        const RegOpenKeyExW = advapi32.getExportByName('RegOpenKeyExW');
        if (!RegOpenKeyExW) {
            console.log("[-] RegOpenKeyExW function not found");
            return;
        }

        Interceptor.attach(RegOpenKeyExW, {
            onEnter: function(args) {
                try {
                    const lpSubKey = args[1];
                    const samDesired = args[3];

                    if (lpSubKey && !lpSubKey.isNull()) {
                        const subKey = lpSubKey.readUtf16String();
                        
                        // 检查是否包含特定注册表路径
                        const registryPath = "{{registry_path}}";
                        const isTarget = registryPath !== "" && subKey.includes(registryPath);
                        
                        if (isTarget) {
                            console.log("[TARGET REGISTRY] " + "=".repeat(50));
                            console.log(`KEY: ${subKey}`);
                            console.log(`ACCESS: 0x${samDesired.toString(16)}`);
                            console.log("=".repeat(50));
                        } else {
                            console.log(`[RegOpenKeyExW] ${subKey}`);
                        }
                    }
                } catch (e) {
                    console.log(`[RegOpenKeyExW Error] ${e.message}`);
                }
            }
        });

        console.log("[✓] RegOpenKeyExW monitor active");
    } catch (e) {
        console.log(`[RegOpenKeyExW Setup Error] ${e.message}`);
    }
}

/**
 * 监控RegSetValueExW API的使用情况
 * 对特定注册表路径有特征输出
 */
function monitorRegistry_RegSetValueExW() {
    console.log("[+] Setting up RegSetValueExW monitor...");

    const advapi32 = Process.getModuleByName('advapi32.dll');
    if (!advapi32) {
        console.log("[-] advapi32.dll module not found");
        return;
    }

    try {
        const RegSetValueExW = advapi32.getExportByName('RegSetValueExW');
        if (!RegSetValueExW) {
            console.log("[-] RegSetValueExW function not found");
            return;
        }

        Interceptor.attach(RegSetValueExW, {
            onEnter: function(args) {
                try {
                    const lpValueName = args[1];
                    const dwType = args[3];
                    const lpData = args[4];
                    const cbData = args[5];

                    if (lpValueName && !lpValueName.isNull()) {
                        const valueName = lpValueName.readUtf16String();
                        
                        let data = "";
                        let dataLength = cbData.toInt32();
                        
                        if (lpData && !lpData.isNull()) {
                            try {
                                const type = dwType.toInt32();
                                switch (type) {
                                    case 1: // REG_SZ
                                        data = lpData.readUtf16String();
                                        break;
                                    case 2: // REG_EXPAND_SZ
                                        data = lpData.readUtf16String() + " [EXPAND]";
                                        break;
                                    case 3: // REG_BINARY
                                        const bytes = lpData.readByteArray(Math.min(dataLength, 16));
                                        data = "[BINARY] " + Array.from(new Uint8Array(bytes))
                                            .map(b => ('0' + b.toString(16)).slice(-2)).join(' ');
                                        if (dataLength > 16) data += "...";
                                        break;
                                    case 4: // REG_DWORD
                                        data = "[DWORD] 0x" + lpData.readU32().toString(16);
                                        break;
                                    case 7: // REG_MULTI_SZ
                                        data = "[MULTI_SZ] " + lpData.readUtf16String();
                                        break;
                                    default:
                                        data = `[TYPE_${type}] ${dataLength} bytes`;
                                }
                            } catch (e) {
                                data = `[BINARY] ${dataLength} bytes`;
                            }
                        }

                        // 检查是否涉及特定注册表路径
                        const registryPath = "{{registry_path}}";
                        const isTarget = registryPath !== "" && valueName.includes(registryPath);
                        
                        if (isTarget) {
                            console.log("[TARGET REGISTRY WRITE] " + "=".repeat(50));
                            console.log(`VALUE: ${valueName}`);
                            console.log(`TYPE: 0x${dwType.toString(16)}`);
                            console.log(`DATA: ${data}`);
                            console.log(`LENGTH: ${dataLength}`);
                            console.log("=".repeat(50));
                        } else {
                            console.log(`[RegSetValueExW] ${valueName} = ${data}`);
                        }
                    }
                } catch (e) {
                    console.log(`[RegSetValueExW Error] ${e.message}`);
                }
            }
        });

        console.log("[✓] RegSetValueExW monitor active");
    } catch (e) {
        console.log(`[RegSetValueExW Setup Error] ${e.message}`);
    }
}

/**
 * 主函数：执行所有注册表监控
 */
function monitorRegistry() {
    console.log("=".repeat(60));
    console.log("Starting Windows Registry Monitor");
    console.log("=".repeat(60));

    monitorRegistry_RegOpenKeyExW();
    monitorRegistry_RegSetValueExW();

    console.log("[✓] All registry monitors initialized");
    console.log("=".repeat(60));
}

// 执行监控
monitorRegistry();