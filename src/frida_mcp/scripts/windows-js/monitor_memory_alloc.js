// Windows内存申请监控脚本 - 监控VirtualAlloc、HeapCreate、CreateFiber等API
// 当检测到RX/RWX类型的可执行内存时，通过Interceptor监控首次执行或权限变更后再dump

// 确保 windows_base_utils.js 已加载

/**
 * Windows内存保护常量 (PAGE_*)
 */
const MEMORY_PROTECTION_FLAGS = {
    0x10: "PAGE_EXECUTE",                // X
    0x20: "PAGE_EXECUTE_READ",           // RX
    0x40: "PAGE_EXECUTE_READWRITE",      // RWX
    0x80: "PAGE_EXECUTE_WRITECOPY",      // WX
    0x01: "PAGE_NOACCESS",
    0x02: "PAGE_READONLY",               // R
    0x04: "PAGE_READWRITE",              // RW
    0x08: "PAGE_WRITECOPY",
    0x100: "PAGE_GUARD",
    0x200: "PAGE_NOCACHE",
    0x400: "PAGE_WRITECOMBINE",
};

const PROT_RX = 0x20;
const PROT_RWX = 0x40;
const PROT_RW = 0x04;
const PROT_R = 0x02;

/**
 * 内存分配类型常量
 */
const MEMORY_ALLOCATION_TYPE = {
    0x00001000: "MEM_COMMIT",
    0x00002000: "MEM_RESERVE",
    0x00010000: "MEM_RESET",
    0x00020000: "MEM_TOP_DOWN",
    0x00080000: "MEM_WRITE_WATCH",
    0x00100000: "MEM_PHYSICAL",
    0x00200000: "MEM_LARGE_PAGES",
    0x00400000: "MEM_4MB_PAGES",
};

/**
 * 跟踪的内存区域存储
 * key: address (string), value: {size, originalProtect, api, timestamp, status}
 * status: 'pending' | 'monitored' | 'dumped' | 'transitioned'
 */
const trackedMemoryRegions = new Map();

/**
 * 解析内存保护标志
 */
function parseMemoryProtection(protect) {
    const baseProtect = protect & 0xFF;
    const flags = [];
    if (MEMORY_PROTECTION_FLAGS[baseProtect]) {
        flags.push(MEMORY_PROTECTION_FLAGS[baseProtect]);
    }
    for (const [flag, name] of Object.entries(MEMORY_PROTECTION_FLAGS)) {
        const flagValue = parseInt(flag);
        if (flagValue >= 0x100 && (protect & flagValue)) {
            flags.push(name);
        }
    }
    return flags.length > 0 ? flags.join('|') : `0x${protect.toString(16)}`;
}

/**
 * 解析内存分配类型
 */
function parseAllocationType(allocType) {
    const flags = [];
    for (const [flag, name] of Object.entries(MEMORY_ALLOCATION_TYPE)) {
        if (allocType & parseInt(flag)) {
            flags.push(name);
        }
    }
    return flags.length > 0 ? flags.join('|') : `0x${allocType.toString(16)}`;
}

/**
 * 检查是否为可执行保护
 */
function isExecutableProtection(protect) {
    const base = protect & 0xFF;
    return base === PROT_RX || base === PROT_RWX || base === 0x10; // X, RX, RWX
}

/**
 * 检查是否为可写保护
 */
function isWritableProtection(protect) {
    const base = protect & 0xFF;
    return base === PROT_RW || base === PROT_RWX || base === 0x08; // RW, RWX, WC
}

/**
 * 发送内存dump请求
 */
function requestMemoryDump(address, size, apiName, reason, extraInfo) {
    const MAX_DUMP_SIZE = 10 * 1024 * 1024; // 最大 dump 10MB
    
    // 限制 dump 大小
    let actualSize = size;
    if (size > MAX_DUMP_SIZE) {
        console.log(`[MemoryMonitor] Region too large (${(size / 1024 / 1024).toFixed(2)}MB), dump limited to 10MB`);
        actualSize = MAX_DUMP_SIZE;
    }
    
    const filename = `mem_${apiName}_${Process.id}_${Date.now()}_0x${address.toString(16)}.bin`;
    
    // 读取内存数据
    let memoryData = null;
    try {
        memoryData = Memory.readByteArray(address, actualSize);
    } catch (e) {
        console.log(`[MemoryMonitor] Failed to read memory at 0x${address.toString(16)}: ${e.message}`);
        return null;
    }
    
    // 只发送 Python 端需要的字段
    send({
        type: "memory_dump",
        filename: filename,
        pid: Process.id
    }, memoryData);
    
    // 其他信息以单行日志形式输出
    console.log(`[MemoryMonitor] Dump info: addr=0x${address.toString(16)}, size=${actualSize}${size > MAX_DUMP_SIZE ? '/' + size : ''}, api=${apiName}, reason=${reason}`);
    return filename;
}

/**
 * 发送可执行内存告警
 */
function sendExecutableAlert(address, size, protection, apiName, action, extraInfo) {
    let logMsg = "[EXECUTABLE_MEMORY_ALERT]\n" +
        "  API: " + apiName + "\n" +
        "  Address: " + address.toString() + "\n" +
        "  Size: " + size + "\n" +
        "  Protection: " + parseMemoryProtection(protection) + "\n" +
        "  Action: " + action + "\n" +
        "  Timestamp: " + Date.now();
    if (extraInfo) {
        logMsg += "\n  ExtraInfo: " + JSON.stringify(extraInfo);
    }
    console.log(logMsg);
}

/**
 * 从上下文获取返回地址（x86/x64）
 */
function getReturnAddress(context) {
    try {
        // x64: 返回地址在 [rsp]，x86: 返回地址在 [esp]
        const sp = context.rsp || context.esp;
        if (sp) {
            return Memory.readPointer(sp);
        }
    } catch (e) {
        // 读取失败
    }
    return null;
}

/**
 * 创建Interceptor监听首次执行
 * 当执行流跳转到目标内存时触发dump
 */
function monitorFirstExecution(address, size, apiName, originalInfo) {
    const addrStr = address.toString();
    
    // 避免重复监控同一区域
    if (trackedMemoryRegions.has(addrStr)) {
        const existing = trackedMemoryRegions.get(addrStr);
        if (existing.status === 'monitored' || existing.status === 'dumped') {
            return;
        }
    }
    
    try {
        // 在内存起始地址设置Interceptor
        const interceptor = Interceptor.attach(address, {
            onEnter: function(args) {
                const addrStr = address.toString();
                const region = trackedMemoryRegions.get(addrStr);
                
                if (region && region.status !== 'dumped') {
                    region.status = 'dumped';
                    trackedMemoryRegions.set(addrStr, region);
                    
                    // 获取返回地址
                    const returnAddr = getReturnAddress(this.context);
                    const callerStr = returnAddr ? returnAddr.toString() : 'unknown';
                    
                    // 请求dump
                    requestMemoryDump(
                        address, 
                        size, 
                        apiName, 
                        "First execution intercepted",
                        {
                            originalProtect: parseMemoryProtection(region.originalProtect),
                            caller: callerStr
                        }
                    );
                    
                    sendExecutableAlert(address, size, region.originalProtect, apiName, "dump_on_first_execute", {
                        caller: callerStr
                    });
                    
                    // 执行一次后可以选择detach
                    // interceptor.detach();
                }
            }
        });
        
        trackedMemoryRegions.set(addrStr, {
            address: address,
            size: size,
            originalProtect: originalInfo.protect,
            api: apiName,
            timestamp: Date.now(),
            status: 'monitored',
            interceptor: interceptor
        });
        
    } catch (e) {
        // Interceptor设置失败（可能地址不可执行），直接dump
        requestMemoryDump(address, size, apiName, "Interceptor failed, direct dump", {error: e.message});
    }
}

/**
 * 检查是否为权限转换场景
 * RW -> RX 或 RWX -> RX
 */
function isProtectionTransition(oldProtect, newProtect) {
    const oldBase = oldProtect & 0xFF;
    const newBase = newProtect & 0xFF;
    
    // RW -> RX
    const isRwToRx = (oldBase === PROT_RW || oldBase === PROT_RWX) && newBase === PROT_RX;
    // RWX -> RX
    const isRwxToRx = oldBase === PROT_RWX && newBase === PROT_RX;
    
    return isRwToRx || isRwxToRx;
}

/**
 * 创建内存分配API监控的onEnter回调
 */
function createMemoryAllocOnEnter(apiName) {
    return function(args) {
        let address = ptr(0);
        let size = 0;
        let protect = 0;
        let allocType = 0;

        switch (apiName) {
            case "VirtualAlloc":
                address = safeArg(args, 0);
                size = safeToUInt32(safeArg(args, 1));
                allocType = safeToUInt32(safeArg(args, 2));
                protect = safeToUInt32(safeArg(args, 3));
                break;

            case "VirtualAllocEx":
                address = safeArg(args, 1);
                size = safeToUInt32(safeArg(args, 2));
                allocType = safeToUInt32(safeArg(args, 3));
                protect = safeToUInt32(safeArg(args, 4));
                break;

            case "VirtualProtect":
                address = safeArg(args, 0);
                size = safeToUInt32(safeArg(args, 1));
                protect = safeToUInt32(safeArg(args, 2));
                break;

            case "VirtualProtectEx":
                address = safeArg(args, 1);
                size = safeToUInt32(safeArg(args, 2));
                protect = safeToUInt32(safeArg(args, 3));
                break;

            case "HeapCreate":
                const heapFlags = safeToUInt32(safeArg(args, 0));
                size = safeToUInt32(safeArg(args, 2));
                if (heapFlags & 0x00020000) {
                    protect = PROT_RWX;
                }
                break;

            case "HeapAlloc":
                size = safeToUInt32(safeArg(args, 2));
                break;

            case "CreateFiber":
                size = safeToUInt32(safeArg(args, 0));
                break;

            case "CreateFiberEx":
                size = safeToUInt32(safeArg(args, 1));
                break;

            case "MapViewOfFile":
            case "MapViewOfFileEx":
                size = safeToUInt32(safeArg(args, 4));
                break;
        }

        // 保存数据供onLeave使用
        this.memoryData = {
            apiName,
            inputAddress: address,
            size,
            protect,
            allocType,
            isExecutableRequest: isExecutableProtection(protect)
        };
        
        // 输出当前API调用信息
        const protStr = parseMemoryProtection(protect);
        const typeStr = allocType ? parseAllocationType(allocType) : '-';
        console.log(`[MemoryMonitor] ${apiName}: addr=${address.toString()}, size=${size}, prot=${protStr}, type=${typeStr}`);
    };
}

/**
 * 创建内存分配API监控的onLeave回调
 */
function createMemoryAllocOnLeave(apiName) {
    return function(retval) {
        const data = this.memoryData;
        if (!data) return;

        try {
            const returnedAddress = retval;
            const success = !returnedAddress.isNull();
            
            // 确定实际地址
            let actualAddress;
            if (apiName.includes("VirtualProtect")) {
                actualAddress = data.inputAddress;
            } else {
                actualAddress = returnedAddress;
            }
            
            if (!success || actualAddress.isNull()) {
                return;
            }

            // 查询实际内存保护
            let actualProtect = data.protect;
            let shouldMonitor = false;
            let dumpImmediately = false;
            let reason = "";
            let extraInfo = {};

            try {
                const memInfo = Memory.queryProtection(actualAddress);
                if (memInfo) {
                    actualProtect = memInfo.protection;
                }
            } catch (e) {
                // 查询失败，使用请求时的保护值
            }

            // 检查是否为可执行内存
            if (isExecutableProtection(actualProtect)) {
                // 检查是否已存在跟踪记录（可能是VirtualProtect转换）
                const addrStr = actualAddress.toString();
                const existingRegion = trackedMemoryRegions.get(addrStr);
                
                if (existingRegion) {
                    // 检查是否为权限转换场景
                    if (isProtectionTransition(existingRegion.originalProtect, actualProtect)) {
                        // RW->RX 或 RWX->RX 转换，立即dump
                        dumpImmediately = true;
                        reason = `Protection transition: ${parseMemoryProtection(existingRegion.originalProtect)} -> ${parseMemoryProtection(actualProtect)}`;
                        existingRegion.status = 'transitioned';
                        trackedMemoryRegions.set(addrStr, existingRegion);
                        
                        extraInfo = {
                            previousProtect: parseMemoryProtection(existingRegion.originalProtect),
                            newProtect: parseMemoryProtection(actualProtect),
                            originalApi: existingRegion.api
                        };
                    } else if (existingRegion.status === 'monitored') {
                        // 已经在监控中，跳过
                        return;
                    }
                } else {
                    // 新分配的可执行内存
                    if (isWritableProtection(actualProtect)) {
                        // RWX - 设置Interceptor等待首次执行
                        shouldMonitor = true;
                        reason = "RWX memory allocated, monitoring first execution";
                    } else {
                        // RX - 可能是已经准备好的代码，立即dump
                        dumpImmediately = true;
                        reason = "RX memory allocated";
                    }
                }

                // 发送告警（包含完整信息）
                sendExecutableAlert(actualAddress, data.size, actualProtect, apiName, 
                    shouldMonitor ? "monitor_first_execute" : (dumpImmediately ? "immediate_dump" : "transition"),
                    extraInfo
                );

                // 执行dump或设置监控
                if (dumpImmediately) {
                    requestMemoryDump(actualAddress, data.size, apiName, reason, extraInfo);
                } else if (shouldMonitor) {
                    monitorFirstExecution(actualAddress, data.size, apiName, {
                        protect: actualProtect,
                        api: apiName
                    });
                }
            }

        } catch (e) {
            // 静默处理错误，避免重复日志
        }
    };
}

/**
 * 监控单个内存分配API
 */
function monitorMemoryAllocApi(apiName, moduleName) {
    if (!moduleName) {
        const kernelBaseApis = ["VirtualAlloc", "VirtualAllocEx", "VirtualProtect", "VirtualProtectEx", 
                              "HeapCreate", "HeapAlloc", "CreateFiber", "CreateFiberEx", 
                              "MapViewOfFile", "MapViewOfFileEx"];
        moduleName = kernelBaseApis.includes(apiName) ? "kernelbase.dll" : "kernel32.dll";
    }

    try {
        const module = Process.getModuleByName(moduleName);
        if (!module) return;
        
        const apiAddress = module.getExportByName(apiName);
        if (!apiAddress) return;

        Interceptor.attach(apiAddress, {
            onEnter: createMemoryAllocOnEnter(apiName),
            onLeave: createMemoryAllocOnLeave(apiName)
        });
        
    } catch (e) {
        // 静默处理加载失败
    }
}

/**
 * 监控多个内存分配API
 */
function monitorMemoryAllocApis(apiNames) {
    const defaultApis = [
        "VirtualAlloc", "VirtualAllocEx", "VirtualProtect", "VirtualProtectEx",
        "HeapCreate", "HeapAlloc", "CreateFiber", "CreateFiberEx",
        "MapViewOfFile", "MapViewOfFileEx"
    ];

    const apisToMonitor = apiNames || defaultApis;

    apisToMonitor.forEach(apiName => {
        monitorMemoryAllocApi(apiName);
    });

    // 只发送一次初始化完成消息
    console.log(`[MemoryMonitor] Initialized, monitoring ${apisToMonitor.length} APIs: ${apisToMonitor.join(", ")}`);
}

// ==================== 启动监控 ====================
monitorMemoryAllocApis();
