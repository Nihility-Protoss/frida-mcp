/**
 * 检查是否为目标路径
 * @param {string} targetPath - 目标路径关键字
 * @param {string} currentPath - 当前路径
 * @returns {boolean} 是否匹配
 */
function isTargetPath(targetPath, currentPath) {
    // 如果targetPath为空或null，则匹配所有路径
    if (!targetPath || targetPath === "") {
        return false;
    }
    if (!currentPath) return false;
    return currentPath.toLowerCase().includes(targetPath.toLowerCase());
}

// 工具函数：安全读取字符串（自动区分 A/W 版本 + 崩溃防护）
function safeReadString(ptr, isWide) {
    if (!ptr || ptr.isNull()) return "";
    try {
        return isWide ? ptr.readUtf16String() : ptr.readUtf8String();
    } catch (e) {
        return "[invalid_ptr]";
    }
}

// 工具函数：安全转换指针为数值
function safeToUInt32(ptr, defaultValue = 0) {
    if (!ptr || ptr.isNull()) return defaultValue;
    try {
        return ptr.toUInt32();
    } catch (e) {
        return defaultValue;
    }
}

// 工具函数：安全获取参数（避免索引越界）
function safeArg(args, index, defaultPtr = ptr(0)) {
    return (args && index < args.length) ? args[index] : defaultPtr;
}
// 🔧 工具函数：格式化句柄（便于日志追踪）
function formatHandle(h) {
    return h && !h.isNull() ? "0x" + h.toString(16) : "NULL";
}

// Windows API监控脚本
function monitorApi(moduleName, apiName) {
    console.log(`[+] Monitoring ${moduleName}!${apiName}`);

    try {
        const module = Process.getModuleByName(moduleName);
        if (!module) {
            console.log(`[-] Module ${moduleName} not found`);
            return;
        }

        const apiAddress = module.getExportByName(apiName);
        if (!apiAddress) {
            console.log(`[-] API ${apiName} not found in ${moduleName}`);
            return;
        }

        Interceptor.attach(apiAddress, {
            onEnter: function(args) {
                try {
                    console.log(`[+] ${apiName} called`);
                    
                    // 打印参数
                    for (let i = 0; i < 6; i++) {
                        if (args[i]) {
                            console.log(`[+] arg[${i}]: 0x${args[i].toString(16)}`);
                        }
                    }
                    
                    // 保存参数用于onLeave
                    this.args = [];
                    for (let i = 0; i < 6; i++) {
                        this.args[i] = args[i];
                    }
                } catch (e) {
                    console.log(`[+] Error in onEnter: ${e.message}`);
                }
            },
            onLeave: function(retval) {
                try {
                    console.log(`[+] ${apiName} returned: 0x${retval.toString(16)}`);
                    
                    // 如果返回的是字符串，打印字符串内容
                    if (retval.toInt32() > 0) {
                        try {
                            const str = Memory.readUtf8String(ptr(retval.toInt32()));
                            console.log(`[+] Return string: ${str}`);
                        } catch (e) {
                            // 不是字符串，忽略
                        }
                    }
                } catch (e) {
                    console.log(`[+] Error in onLeave: ${e.message}`);
                }
            }
        });
        
        console.log(`[+] Successfully attached to ${moduleName}!${apiName}`);
    } catch (e) {
        console.log(`[+] Error setting up API monitor: ${e.message}`);
    }
}