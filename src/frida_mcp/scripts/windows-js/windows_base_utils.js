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
//
// 功能：监控指定模块中的API函数调用
//
// 参数：
//   moduleName: 模块名称 (例如: "kernel32.dll", "user32.dll")
//   apiName: API函数名称 (例如: "CreateFileW", "MessageBoxA")
//   onEnterCallback: (可选) 自定义onEnter回调函数，接收args参数
//   onLeaveCallback: (可选) 自定义onLeave回调函数，接收retval参数
//
// 使用示例：
//
// 1. 使用默认行为：
//    monitorApi("kernel32.dll", "CreateFileW");
//
// 2. 自定义onEnter回调：
//    monitorApi("kernel32.dll", "CreateFileW", function(args) {
//        console.log("Custom onEnter: filename = " + Memory.readUtf16String(args[0]));
//        this.filename = Memory.readUtf16String(args[0]);
//    });
//
// 3. 自定义onLeave回调：
//    monitorApi("kernel32.dll", "CreateFileW", null, function(retval) {
//        console.log("Custom onLeave: handle = " + retval);
//    });
//
// 4. 完全自定义：
//    monitorApi("kernel32.dll", "CreateFileW",
//        function(args) { console.log("Entering CreateFileW"); },
//        function(retval) { console.log("Leaving CreateFileW"); }
//    );
function monitorApi(moduleName, apiName, onEnterCallback, onLeaveCallback) {
    // console.log(`[+] Monitoring ${moduleName}!${apiName}`);

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

        // 默认的onEnter处理函数
        const defaultOnEnter = function(args) {
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
        };

        // 默认的onLeave处理函数
        const defaultOnLeave = function(retval) {
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
        };

        // 使用提供的回调或默认处理函数
        const onEnterHandler = typeof onEnterCallback === 'function' ? onEnterCallback : defaultOnEnter;
        const onLeaveHandler = typeof onLeaveCallback === 'function' ? onLeaveCallback : defaultOnLeave;

        Interceptor.attach(apiAddress, {
            onEnter: onEnterHandler,
            onLeave: onLeaveHandler
        });
        
        console.log(`[+] Successfully attached to ${moduleName}!${apiName}`);
    } catch (e) {
        console.log(`[+] Error setting up API monitor: ${e.message}`);
    }
}