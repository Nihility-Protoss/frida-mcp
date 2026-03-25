/**
 * 检查是否为目标路径
 * @param {string} targetPath - 目标路径关键字
 * @param {string} currentPath - 当前路径
 * @returns {boolean} 是否匹配
 */
function isTargetPath(targetPath, currentPath) {
    if (!targetPath || targetPath === "") {
        return true;
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
    if (!args || index < 0) return defaultPtr;
    const arg = args[index];
    return arg || defaultPtr;
}

// 工具函数：格式化句柄（便于日志追踪）
function formatHandle(h) {
    return h && !h.isNull() ? "0x" + h.toString(16) : "NULL";
}

/**
 * Safely reads raw bytes from pointer.
 * Compatible with Frida 17 (NativePointer.readByteArray).
 */
function readBytesSafe(ptrValue, size) {
    if (!ptrValue || ptrValue.isNull() || size <= 0) return new Uint8Array(0);
    try {
        const buf = ptrValue.readByteArray(size);
        return buf ? new Uint8Array(buf) : new Uint8Array(0);
    } catch (e) {
        return new Uint8Array(0);
    }
}

/**
 * Converts bytes to hex string.
 */
function bytesToHex(bytes) {
    if (!bytes || bytes.length === 0) return "";
    let out = "";
    for (let i = 0; i < bytes.length; i++) {
        out += bytes[i].toString(16).padStart(2, "0");
    }
    return out;
}

/**
 * Converts bytes to readable ASCII text.
 * Non-printable bytes are replaced with '.'.
 */
function bytesToText(bytes) {
    if (!bytes || bytes.length === 0) return "";
    let out = "";
    for (let i = 0; i < bytes.length; i++) {
        const b = bytes[i];
        out += (b >= 0x20 && b <= 0x7e) ? String.fromCharCode(b) : ".";
    }
    return out;
}

/**
 * Reads ANSI string by explicit length.
 * Supports 0xFFFFFFFF as null-terminated mode.
 */
function readAnsiByLength(ptrValue, lengthDword) {
    if (!ptrValue || ptrValue.isNull()) return "";
    try {
        if (lengthDword === 0xffffffff) return safeReadString(ptrValue, false);
        const len = Number(lengthDword >>> 0);
        if (len === 0) return "";
        return ptrValue.readAnsiString(len);
    } catch (e) {
        return safeReadString(ptrValue, false);
    }
}

/**
 * Reads UTF-16 string by explicit length.
 * Supports 0xFFFFFFFF as null-terminated mode.
 */
function readWideByLength(ptrValue, lengthDword) {
    if (!ptrValue || ptrValue.isNull()) return "";
    try {
        if (lengthDword === 0xffffffff) return safeReadString(ptrValue, true);
        const len = Number(lengthDword >>> 0);
        if (len === 0) return "";
        return ptrValue.readUtf16String(len);
    } catch (e) {
        return safeReadString(ptrValue, true);
    }
}

/**
 * Reads a NULL-terminated WCHAR* list from WCHAR**.
 */
function readWideStringList(ppWideStrings, maxCount = 32) {
    if (!ppWideStrings || ppWideStrings.isNull()) return [];
    const list = [];
    const step = Process.pointerSize;
    try {
        for (let i = 0; i < maxCount; i++) {
            const p = Memory.readPointer(ppWideStrings.add(i * step));
            if (!p || p.isNull()) break;
            list.push(safeReadString(p, true));
        }
    } catch (e) {
        // Ignore parse errors.
    }
    return list;
}

// Lazy-hook support for APIs in modules loaded later.
const __activeApiHooks = new Set();   // key: module!api
const __pendingApiHooks = new Map();  // key: module!api -> {moduleName, apiName, onEnter, onLeave}
let __moduleLoadWatcherInstalled = false;
let __moduleObserverInstalled = false;
let __pendingRetryTimerStarted = false;

function __makeApiHookKey(moduleName, apiName) {
    return `${String(moduleName || "").toLowerCase()}!${apiName}`;
}

function __attachApiNow(moduleName, apiName, onEnterHandler, onLeaveHandler) {
    const key = __makeApiHookKey(moduleName, apiName);
    if (__activeApiHooks.has(key)) return {attached: true, reason: "already_attached"};

    const module = Process.findModuleByName(moduleName);
    if (!module) return {attached: false, reason: "module_not_loaded"};

    let apiAddress = null;
    try {
        apiAddress = module.getExportByName(apiName);
    } catch (e) {
        return {attached: false, reason: "export_not_found"};
    }
    if (!apiAddress) return {attached: false, reason: "export_not_found"};

    Interceptor.attach(apiAddress, {
        onEnter: onEnterHandler,
        onLeave: onLeaveHandler
    });

    __activeApiHooks.add(key);
    __pendingApiHooks.delete(key);
    console.log(`[+] Successfully attached to ${moduleName}!${apiName}`);
    return {attached: true, reason: "attached"};
}

function __retryPendingApiHooks() {
    if (__pendingApiHooks.size === 0) return;
    for (const [_, item] of __pendingApiHooks) {
        try {
            __attachApiNow(item.moduleName, item.apiName, item.onEnter, item.onLeave);
        } catch (e) {
            const errText = (e && e.stack) ? e.stack : String(e);
            console.log(`[!] __retryPendingApiHooks failed for ${item.moduleName}!${item.apiName}: ${errText}`);
            // Keep pending until next retry.
        }
    }
}

function __ensurePendingRetryTimer() {
    if (__pendingRetryTimerStarted) return;
    __pendingRetryTimerStarted = true;
    setInterval(function () {
        try {
            __retryPendingApiHooks();
        } catch (e) {
            const errText = (e && e.stack) ? e.stack : String(e);
            console.log(`[!] pending hook retry timer failed: ${errText}`);
        }
    }, 1000);
}

function __ensureModuleObserver() {
    if (__moduleObserverInstalled) return;
    if (typeof Process.attachModuleObserver !== "function") return;
    try {
        Process.attachModuleObserver({
            onAdded: function () {
                __retryPendingApiHooks();
            }
        });
        __moduleObserverInstalled = true;
    } catch (e) {
        const errText = (e && e.stack) ? e.stack : String(e);
        console.log(`[!] failed to install module observer: ${errText}`);
    }
}

function __ensureModuleLoadWatcher() {
    if (__moduleLoadWatcherInstalled) return;
    __moduleLoadWatcherInstalled = true;

    const tryInstall = function (moduleName, apiName) {
        try {
            const mod = Process.findModuleByName(moduleName);
            if (!mod) return false;
            const fn = mod.getExportByName(apiName);
            if (!fn) return false;
            Interceptor.attach(fn, {
                onLeave: function () {
                    __retryPendingApiHooks();
                }
            });
            return true;
        } catch (e) {
            const errText = (e && e.stack) ? e.stack : String(e);
            console.log(`[!] __ensureModuleLoadWatcher tryInstall failed for ${moduleName}!${apiName}: ${errText}`);
            return false;
        }
    };

    tryInstall("kernel32.dll", "LoadLibraryA");
    tryInstall("kernel32.dll", "LoadLibraryW");
    tryInstall("kernel32.dll", "LoadLibraryExA");
    tryInstall("kernel32.dll", "LoadLibraryExW");
    tryInstall("kernelbase.dll", "LoadLibraryA");
    tryInstall("kernelbase.dll", "LoadLibraryW");
    tryInstall("kernelbase.dll", "LoadLibraryExA");
    tryInstall("kernelbase.dll", "LoadLibraryExW");
    tryInstall("ntdll.dll", "LdrLoadDll");

    __ensureModuleObserver();
    __ensurePendingRetryTimer();
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
        // Default onEnter callback
        const defaultOnEnter = function (args) {
            try {
                console.log(`[+] ${apiName} called`);

                // Dump first 6 arguments
                for (let i = 0; i < 6; i++) {
                    if (args[i]) {
                        console.log(`[+] arg[${i}]: 0x${args[i].toString(16)}`);
                    }
                }

                // Save arguments for onLeave
                this.args = [];
                for (let i = 0; i < 6; i++) {
                    this.args[i] = args[i];
                }
            } catch (e) {
                console.log(`[+] Error in onEnter: ${e.message}`);
            }
        };

        // Default onLeave callback
        const defaultOnLeave = function (retval) {
            try {
                console.log(`[+] ${apiName} returned: 0x${retval.toString(16)}`);

                // Try to interpret positive return values as pointers to UTF-8 strings
                if (retval.toInt32() > 0) {
                    try {
                        const str = Memory.readUtf8String(ptr(retval.toInt32()));
                        console.log(`[+] Return string: ${str}`);
                    } catch (e) {
                        // Ignore if return value is not a valid string pointer
                    }
                }
            } catch (e) {
                console.log(`[+] Error in onLeave: ${e.message}`);
            }
        };

        // Use custom callbacks when provided, otherwise fallback to defaults
        const onEnterHandler = typeof onEnterCallback === 'function' ? onEnterCallback : defaultOnEnter;
        const onLeaveHandler = typeof onLeaveCallback === 'function' ? onLeaveCallback : defaultOnLeave;
        const key = __makeApiHookKey(moduleName, apiName);

        const module = Process.findModuleByName(moduleName);
        if (!module) {
            console.log(`[-] Module ${moduleName} not found`);
            __pendingApiHooks.set(key, {
                moduleName: moduleName,
                apiName: apiName,
                onEnter: onEnterHandler,
                onLeave: onLeaveHandler
            });
            __ensureModuleLoadWatcher();
            return;
        }

        let apiAddress;
        try {
            apiAddress = module.getExportByName(apiName);
        } catch (e) {
            apiAddress = null;
        }
        if (!apiAddress) {
            console.log(`[-] API ${apiName} not found in ${moduleName}`);
            __pendingApiHooks.set(key, {
                moduleName: moduleName,
                apiName: apiName,
                onEnter: onEnterHandler,
                onLeave: onLeaveHandler
            });
            __ensureModuleLoadWatcher();
            return;
        }

        Interceptor.attach(apiAddress, {
            onEnter: onEnterHandler,
            onLeave: onLeaveHandler
        });

        __activeApiHooks.add(key);
        __pendingApiHooks.delete(key);
        console.log(`[+] Successfully attached to ${moduleName}!${apiName}`);
    } catch (e) {
        console.log(`[+] Error setting up API monitor: ${e.message}`);
    }
}
