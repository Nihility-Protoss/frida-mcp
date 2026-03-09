// Windows注册表监控API
// 模板变量：
//   {{registry_path}} - 要监控的注册表路径关键字（可以为空，监控所有路径）
//   {{api_name}} - 要监控的注册表API名称 (如 RegOpenKeyExW, RegSetValueExW, RegQueryValueExW 等)
/**
 * 注册表数据类型映射
 */
const REGISTRY_TYPES = {
    0: "REG_NONE",
    1: "REG_SZ",
    2: "REG_EXPAND_SZ",
    3: "REG_BINARY",
    4: "REG_DWORD",
    5: "REG_DWORD_BIG_ENDIAN",
    6: "REG_LINK",
    7: "REG_MULTI_SZ",
    8: "REG_RESOURCE_LIST",
    9: "REG_FULL_RESOURCE_DESCRIPTOR",
    10: "REG_RESOURCE_REQUIREMENTS_LIST",
    11: "REG_QWORD"
};

/**
 * 解析注册表数据为可读格式
 * @param {NativePointer} lpData - 数据指针
 * @param {number} dwType - 数据类型
 * @param {number} cbData - 数据长度
 * @returns {string} 可读格式的数据字符串
 */
function parseRegistryData(lpData, dwType, cbData) {
    if (!lpData || lpData.isNull()) return "null";

    const dataLength = cbData.toInt32();
    const type = dwType.toInt32();

    try {
        switch (type) {
            case 1: // REG_SZ
                return lpData.readUtf16String();
            case 2: // REG_EXPAND_SZ
                return lpData.readUtf16String() + " [EXPAND]";
            case 3: // REG_BINARY
                if (dataLength <= 0) return "[BINARY] 0 bytes";
                const bytes = lpData.readByteArray(Math.min(dataLength, 32));
                const hex = Array.from(new Uint8Array(bytes))
                    .map(b => ('0' + b.toString(16)).slice(-2)).join(' ');
                return `[BINARY] ${hex}${dataLength > 32 ? '...' : ''} (${dataLength} bytes)`;
            case 4: // REG_DWORD
                return `[DWORD] 0x${lpData.readU32().toString(16)} (${lpData.readU32()})`;
            case 7: // REG_MULTI_SZ
                const multiStr = lpData.readUtf16String();
                const parts = multiStr.split('\0').filter(s => s.length > 0);
                return `[MULTI_SZ] ${parts.join(' | ')}`;
            case 11: // REG_QWORD
                return `[QWORD] 0x${lpData.readU64().toString(16)}`;
            default:
                return `[TYPE_${type} (${REGISTRY_TYPES[type] || 'UNKNOWN'})] ${dataLength} bytes`;
        }
    } catch (e) {
        return `[BINARY] ${dataLength} bytes (parse error: ${e.message})`;
    }
}

/**
 * 检查是否为目标注册表路径
 * @param {string} targetPath - 目标路径关键字
 * @param {string} currentPath - 当前路径
 * @returns {boolean} 是否匹配
 */
function isTargetRegistry(targetPath, currentPath) {
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

/**
 * 创建注册表API监控的通用onEnter回调
 * @param {string} apiName - API名称
 * @param {string} registryPath - 注册表路径关键字
 * @returns {Function} onEnter回调函数
 */
function createRegistryOnEnter(apiName, registryPath) {
    return function (args) {
        try {
            let keyPath = "";
            let valueName = "";
            let dataType = 0;
            let dataPtr = ptr(0);
            let dataSize = 0;
            let access = 0;

            // 判断是否为 Unicode 版本 (W=wide, A=ansi)
            const isWide = apiName.endsWith('W');

            switch (apiName) {
                // ── 打开/创建键 ─────────────────────────────────────
                case "RegOpenKeyExW":
                case "RegOpenKeyExA":
                case "RegCreateKeyExW":
                case "RegCreateKeyExA":
                    // 参数: [hKey, lpSubKey, Reserved, samDesired, phkResult]
                    keyPath = safeReadString(safeArg(args, 1), isWide);
                    access = safeToUInt32(safeArg(args, 3));
                    break;

                // ── 设置值 ─────────────────────────────────────────
                case "RegSetValueExW":
                case "RegSetValueExA":
                    // 参数: [hKey, lpValueName, Reserved, dwType, lpData, cbData]
                    valueName = safeReadString(safeArg(args, 1), isWide);
                    dataType = safeToUInt32(safeArg(args, 3));
                    dataPtr = safeArg(args, 4);
                    dataSize = safeToUInt32(safeArg(args, 5));
                    // ⚠️ keyPath 无法从参数直接获取，用句柄标记
                    keyPath = "[hKey:" + safeArg(args, 0) + "]";
                    break;

                // ── 查询值 ─────────────────────────────────────────
                case "RegQueryValueExW":
                case "RegQueryValueExA":
                    // 参数: [hKey, lpValueName, Reserved, lpData, lpcbData]
                    valueName = safeReadString(safeArg(args, 1), isWide);
                    dataType = 0;  // 输出参数，此时未知
                    dataPtr = safeArg(args, 3);   // 可能为 NULL（仅查询类型/大小）
                    dataSize = safeToUInt32(safeArg(args, 4));
                    keyPath = "[hKey:" + safeArg(args, 0) + "]";
                    break;

                // ── 删除值 ─────────────────────────────────────────
                case "RegDeleteValueW":
                case "RegDeleteValueA":
                    // 参数: [hKey, lpValueName]
                    valueName = safeReadString(safeArg(args, 1), isWide);
                    keyPath = "[hKey:" + safeArg(args, 0) + "]";
                    break;

                // ── 删除键 ─────────────────────────────────────────
                case "RegDeleteKeyW":
                case "RegDeleteKeyA":
                    // 参数: [hKey, lpSubKey]
                    keyPath = safeReadString(safeArg(args, 1), isWide);
                    break;

                // ── 枚举子键 ───────────────────────────────────────
                case "RegEnumKeyExW":
                case "RegEnumKeyExA":
                    // 参数: [hKey, dwIndex, lpName, lpcchName, ...]
                    // lpName 是输出参数，onEnter 时无法读取，仅记录索引
                    const enumIndex = safeToUInt32(safeArg(args, 1));
                    keyPath = "[enum_index:" + enumIndex + "]";
                    access = safeToUInt32(safeArg(args, 3));  // lpReserved
                    break;

                // ── 枚举值 ─────────────────────────────────────────
                case "RegEnumValueW":
                case "RegEnumValueA":
                    // 参数: [hKey, dwIndex, lpValueName, lpcchValueName, ...]
                    // lpValueName 是输出参数，onEnter 时无法读取
                    const enumValIndex = safeToUInt32(safeArg(args, 1));
                    valueName = "[enum_index:" + enumValIndex + "]";
                    access = safeToUInt32(safeArg(args, 3));  // lpReserved
                    keyPath = "[hKey:" + safeArg(args, 0) + "]";
                    break;

                // ── 关闭键（无字符串参数，仅记录句柄）──────────────
                case "RegCloseKey":
                    keyPath = "[close_hKey:" + safeArg(args, 0) + "]";
                    break;

                // ── 默认：尝试安全读取 ───────────────────────────
                default:
                    const arg1 = safeArg(args, 1);
                    if (arg1 && !arg1.isNull()) {
                        keyPath = safeReadString(arg1, isWide);
                    } else {
                        keyPath = "[unknown_api:" + apiName + "]";
                    }
            }

            // 检查是否为目标路径
            const isTarget = isTargetRegistry(registryPath, keyPath);

            if (isTarget) {
                console.log(`[REGISTRY] Monitoring path: "${registryPath}"`);
                // 有指定路径时显示详细输出
                console.log("[TARGET REGISTRY] " + "=".repeat(60));
                console.log(`API: ${apiName}`);

                if (keyPath) console.log(`KEY: ${keyPath}`);
                if (valueName) console.log(`VALUE: ${valueName}`);
                if (access) console.log(`ACCESS: 0x${access.toString(16)}`);
                if (dataType) {
                    console.log(`TYPE: 0x${dataType.toString(16)} (${REGISTRY_TYPES[dataType.toInt32()] || 'UNKNOWN'})`);
                }
                if (dataPtr && !dataPtr.isNull() && dataSize > 0) {
                    const dataStr = parseRegistryData(dataPtr, dataType, dataSize);
                    console.log(`DATA: ${dataStr}`);
                    console.log(`LENGTH: ${dataSize.toInt32()}`);
                }

                console.log("=".repeat(60));
            } else {
                // 非目标路径的简单输出（非空路径时也触发）
                let output = `[${apiName}]`;
                if (keyPath) output += ` ${keyPath}`;
                if (valueName && valueName !== keyPath) output += `\\${valueName}`;
                console.log(output);
            }

            // 保存数据供onLeave使用
            this.registryData = {
                apiName,
                keyPath,
                valueName,
                dataType,
                dataPtr,
                dataSize,
                isTarget
            };

        } catch (e) {
            console.log(`[${apiName} Error] ${e.message}`);
        }
    };
}

/**
 * 创建注册表API监控的通用onLeave回调
 * @param {string} apiName - API名称
 * @returns {Function} onLeave回调函数
 */
function createRegistryOnLeave(apiName) {
    return function (retval) {
        try {
            const data = this.registryData;
            if (!data) return;

            const success = retval.toInt32() === 0; // ERROR_SUCCESS

            if (data.isTarget) {
                console.log("[TARGET REGISTRY RESULT] " + "-".repeat(50));
                console.log(`API: ${data.apiName}`);
                console.log(`RESULT: ${success ? 'SUCCESS' : 'FAILED (0x' + retval.toString(16) + ')'}`);

                // 对于查询操作，显示返回的数据
                if ((data.apiName.includes('Query') || data.apiName.includes('Enum')) &&
                    success && data.dataPtr && !data.dataPtr.isNull()) {
                    const resultData = parseRegistryData(data.dataPtr, data.dataType, data.dataSize);
                    console.log(`RETURNED DATA: ${resultData}`);
                }

                console.log("-".repeat(50));
            } else {
                if (!success) {
                    console.log(`[${data.apiName} FAILED] 0x${retval.toString(16)}`);
                }
            }
        } catch (e) {
            console.log(`[${apiName} onLeave Error] ${e.message}`);
        }
    };
}

/**
 * 监控特定注册表API
 * @param {string} apiName - API名称 (如 "RegOpenKeyExW", "RegSetValueExW" 等)
 * @param {string} registryPath - 要监控的注册表路径关键字
 * @param {boolean} monitorReturn - 是否监控返回值 (默认: true)
 */
function monitorRegistryApi(apiName, registryPath, monitorReturn = true) {
    console.log(`[+] Monitoring registry API: ${apiName} for path: "${registryPath}"`);

    const onEnter = createRegistryOnEnter(apiName, registryPath);
    const onLeave = monitorReturn ? createRegistryOnLeave(apiName) : null;

    monitorApi("advapi32.dll", apiName, onEnter, onLeave);
}

/**
 * 监控多个注册表API
 * @param {string[]} apiNames - API名称数组
 * @param {string} registryPath - 注册表路径关键字
 */
function monitorRegistryApis(apiNames, registryPath) {
    console.log("=".repeat(70));
    console.log(`Starting Registry Monitor for path: "${registryPath}"`);
    console.log("=".repeat(70));

    apiNames.forEach(apiName => {
        monitorRegistryApi(apiName, registryPath);
    });

    console.log("[✓] All registry API monitors initialized");
    console.log("=".repeat(70));
}
