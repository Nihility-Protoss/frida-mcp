// Windows文件监控API - 模板文件
// 模板变量：
//   {{file_path}} - 要监控的文件路径关键字（可以为空，监控所有路径）
//   {{api_name}} - 要监控的文件API名称 (如 CreateFileW, WriteFile, ReadFile 等)

// 确保 windows_base_utils.js 已加载

/**
 * 文件访问标志 (dwDesiredAccess)
 * 用于 CreateFile, ReadFile, WriteFile 等 API
 * 注意：这些标志可组合使用（位掩码），如 0xC0000000 = GENERIC_READ | GENERIC_WRITE
 */
const FILE_ACCESS_FLAGS = {
    // ── 通用访问权限 (Generic) ─────────────────────────────
    0x80000000: "GENERIC_READ",
    0x40000000: "GENERIC_WRITE",
    0x20000000: "GENERIC_EXECUTE",
    0x10000000: "GENERIC_ALL",

    // ── 标准访问权限 (Standard) ────────────────────────────
    0x00100000: "SYNCHRONIZE",
    0x00080000: "WRITE_OWNER",
    0x00040000: "WRITE_DAC",
    0x00020000: "READ_CONTROL",
    0x00010000: "DELETE",

    // ── 文件特定访问权限 (File-Specific) ───────────────────
    0x00000100: "FILE_WRITE_ATTRIBUTES",
    0x00000080: "FILE_READ_ATTRIBUTES",
    0x00000040: "FILE_DELETE_CHILD",
    0x00000020: "FILE_EXECUTE",           // 同 FILE_TRAVERSE
    0x00000010: "FILE_WRITE_EA",
    0x00000008: "FILE_READ_EA",
    0x00000004: "FILE_APPEND_DATA",       // 同 FILE_ADD_SUBDIRECTORY
    0x00000002: "FILE_WRITE_DATA",        // 同 FILE_ADD_FILE
    0x00000001: "FILE_READ_DATA",         // 同 FILE_LIST_DIRECTORY

    // ── 常用组合别名 (便于识别) ───────────────────────────
    0xC0000000: "GENERIC_READ_WRITE",     // GENERIC_READ | GENERIC_WRITE
    0x120089: "FILE_GENERIC_READ",        // 标准读权限组合
    0x120116: "FILE_GENERIC_WRITE",       // 标准写权限组合
    0x1200A0: "FILE_GENERIC_EXECUTE",     // 标准执行权限组合
};

/**
 * 文件创建/打开标志映射
 */
const FILE_CREATION_FLAGS = {
    1: "CREATE_NEW",
    2: "CREATE_ALWAYS",
    3: "OPEN_EXISTING",
    4: "OPEN_ALWAYS",
    5: "TRUNCATE_EXISTING"
};

/**
 * 解析文件访问标志为可读格式
 * @param {number} accessFlags - 访问标志
 * @returns {string} 可读格式的访问描述
 */
function parseFileAccess(accessFlags) {
    const flags = [];
    for (const [flag, name] of Object.entries(FILE_ACCESS_FLAGS)) {
        if (accessFlags & parseInt(flag)) {
            flags.push(name);
        }
    }
    return flags.length > 0 ? flags.join(' | ') : `0x${accessFlags.toString(16)}`;
}

/**
 * 解析文件创建/打开标志为可读格式
 * @param {number} creationFlags - 创建/打开标志
 * @returns {string} 可读格式的创建描述
 */
function parseFileCreation(creationFlags) {
    return FILE_CREATION_FLAGS[creationFlags] || `0x${creationFlags.toString(16)}`;
}

/**
 * 创建文件API监控的通用onEnter回调
 * @param {string} apiName - API名称
 * @param {string} filePath - 文件路径关键字
 * @returns {Function} onEnter回调函数
 */
function createFileOnEnter(apiName, filePath) {
    return function(args) {
        let fileName = "";
        let accessFlags = 0;
        let creationDisposition = 0;
        let buffer = ptr(0);
        let bytesToReadWrite = 0;
        let offset = 0;
        let handle = ptr(0);

        // 判断是否为 Unicode 版本 (W=wide, A=ansi)
        const isWide = apiName.endsWith('W');

        switch (apiName) {
            // ── 创建/打开文件 ─────────────────────────────────────
            case "CreateFileW":
            case "CreateFileA":
                // 参数: [lpFileName, dwDesiredAccess, dwShareMode, lpSecurityAttributes,
                //        dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile]
                fileName = safeReadString(safeArg(args, 0), isWide);
                accessFlags = safeToUInt32(safeArg(args, 1));
                creationDisposition = safeToUInt32(safeArg(args, 4));
                break;

            // ── 读取文件 ─────────────────────────────────────────
            case "ReadFile":
                // 参数: [hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped]
                handle = safeArg(args, 0);
                fileName = "[HANDLE:" + formatHandle(handle) + "]";  // 句柄无法直接解析为路径
                buffer = safeArg(args, 1);
                bytesToReadWrite = safeToUInt32(safeArg(args, 2));
                // lpNumberOfBytesRead (args[3]) 是输出参数，onEnter 时不可读
                break;

            // ── 写入文件 ─────────────────────────────────────────
            case "WriteFile":
                // 参数: [hFile, lpBuffer, nNumberOfBytesToWrite, lpNumberOfBytesWritten, lpOverlapped]
                handle = safeArg(args, 0);
                fileName = "[HANDLE:" + formatHandle(handle) + "]";
                buffer = safeArg(args, 1);
                bytesToReadWrite = safeToUInt32(safeArg(args, 2));
                break;

            // ── 删除文件 ─────────────────────────────────────────
            case "DeleteFileW":
            case "DeleteFileA":
                // 参数: [lpFileName]
                fileName = safeReadString(safeArg(args, 0), isWide);
                break;

            // ── 移动/重命名文件 ──────────────────────────────────
            case "MoveFileW":
            case "MoveFileA":
                // 参数: [lpExistingFileName, lpNewFileName]
                fileName = safeReadString(safeArg(args, 0), isWide);
                // 如需新路径: let newPath = safeReadString(safeArg(args, 1), isWide);
                break;

            case "MoveFileExW":
            case "MoveFileExA":
                // 参数: [lpExistingFileName, lpNewFileName, dwFlags]
                fileName = safeReadString(safeArg(args, 0), isWide);
                // 如需新路径: let newPath = safeReadString(safeArg(args, 1), isWide);
                // accessFlags = safeToUInt32(safeArg(args, 2));  // dwFlags
                break;

            // ── 复制文件 ─────────────────────────────────────────
            case "CopyFileW":
            case "CopyFileA":
                // 参数: [lpExistingFileName, lpNewFileName, bFailIfExists]
                fileName = safeReadString(safeArg(args, 0), isWide);
                // 如需目标: let dstPath = safeReadString(safeArg(args, 1), isWide);
                break;

            case "CopyFileExW":
            case "CopyFileExA":
                // 参数: [lpExistingFileName, lpNewFileName, lpProgressRoutine, lpData,
                //        pbCancel, dwCopyFlags]
                fileName = safeReadString(safeArg(args, 0), isWide);
                // 如需目标: let dstPath = safeReadString(safeArg(args, 1), isWide);
                // accessFlags = safeToUInt32(safeArg(args, 5));  // dwCopyFlags
                break;

            // ── 关闭句柄（无文件名，仅记录句柄）──────────────────
            case "CloseHandle":
                handle = safeArg(args, 0);
                fileName = "[CLOSE_HANDLE:" + formatHandle(handle) + "]";
                break;

            // ── 默认：尝试安全读取第一个字符串参数 ───────────────
            default:
                const arg0 = safeArg(args, 0);
                if (arg0 && !arg0.isNull()) {
                    fileName = safeReadString(arg0, isWide);
                } else {
                    fileName = "[unknown_api:" + apiName + "]";
                }
        }

        // 检查是否为目标路径
        const isTarget = isTargetPath(filePath, fileName);

        if (isTarget) {
            let output = `[FILE] ${apiName}`;
            if (fileName && fileName !== "[HANDLE]") output += ` ${fileName}`;
            if (accessFlags) output += ` [${parseFileAccess(accessFlags)}]`;
            if (creationDisposition) output += ` [${parseFileCreation(creationDisposition)}]`;
            if (bytesToReadWrite > 0) output += ` (${bytesToReadWrite} bytes)`;
            console.log(output);
        } else {
            let output = `[FILE] ${apiName}`;
            if (fileName && fileName !== "[HANDLE]") output += ` ${fileName}`;
            console.log(output);
        }

        // 保存数据供onLeave使用
        this.fileData = {
            apiName,
            fileName,
            accessFlags,
            creationDisposition,
            buffer,
            bytesToReadWrite,
            isTarget
        };
    };
}

/**
 * 创建文件API监控的通用onLeave回调
 * @param {string} apiName - API名称
 * @returns {Function} onLeave回调函数
 */
function createFileOnLeave(apiName) {
    return function(retval) {
        try {
            const data = this.fileData;
            if (!data) return;

            let success = false;
            let resultDesc = "";

            // 根据API类型判断成功状态
            switch (apiName) {
                case "CreateFileW":
                case "CreateFileA":
                    success = !retval.isNull() && retval.toInt32() !== -1;
                    resultDesc = success ? `HANDLE: 0x${retval.toString(16)}` : "FAILED";
                    break;

                case "ReadFile":
                case "WriteFile":
                    success = retval.toInt32() !== 0;
                    resultDesc = success ? `${data.bytesToReadWrite} bytes processed` : "FAILED";
                    break;

                case "DeleteFileW":
                case "DeleteFileA":
                case "MoveFileW":
                case "MoveFileA":
                case "MoveFileExW":
                case "MoveFileExA":
                case "CopyFileW":
                case "CopyFileA":
                case "CopyFileExW":
                case "CopyFileExA":
                    success = retval.toInt32() !== 0;
                    resultDesc = success ? "SUCCESS" : "FAILED";
                    break;

                default:
                    success = retval.toInt32() !== 0;
                    resultDesc = success ? `SUCCESS (0x${retval.toString(16)})` : "FAILED";
            }

            if (data.isTarget) {
                console.log("[TARGET FILE RESULT] " + "-".repeat(50));
                console.log(`API: ${data.apiName}`);
                console.log(`RESULT: ${resultDesc}`);
                
                if (!success && apiName.includes("CreateFile")) {
                    console.log(`ERROR: ${retval.toInt32()}`);
                }
                
                console.log("[TARGET FILE RESULT] " + "-".repeat(50));
            } else {
                if (!success) {
                    console.log(`[${data.apiName} FAILED] ${retval.toString(16)}`);
                } else if (apiName.includes("CreateFile")){
                    console.log(`[${apiName} Success] [${resultDesc}]`)
                }
            }
        } catch (e) {
            console.log(`[${apiName} onLeave Error] ${e.message}`);
        }
    };
}

/**
 * 创建DeleteFile API的替换函数，阻止删除但返回成功
 * @param {string} apiName - API名称 (DeleteFileW 或 DeleteFileA)
 * @param {string} filePath - 文件路径关键字
 * @returns {Function} 替换函数
 */
function createDeleteFileReplacement(apiName, filePath) {
    return new NativeCallback(function(lpFileName) {
        try {
            const isWide = apiName.endsWith('W');
            const fileName = safeReadString(ptr(lpFileName), isWide);
            
            // 检查是否为目标路径
            const isTarget = isTargetPath(filePath, fileName);
            
            if (isTarget) {
                console.log(`[BLOCKED] ${apiName} ${fileName} - Deletion prevented, returning success`);
                
                // 阻止删除操作，但返回成功 (TRUE = 1)
                return 1; // TRUE - 表示删除成功
            } else {
                // 非目标文件，调用原始函数
                console.log(`[FILE] ${apiName} ${fileName}`);
                
                // 获取原始函数指针
                const module = Process.getModuleByName("kernel32.dll");
                const originalFunc = module.getExportByName(apiName);
                
                // 调用原始函数
                const original = new NativeFunction(originalFunc, 'int', ['pointer']);
                return original(lpFileName);
            }
        } catch (e) {
            console.log(`[${apiName} Error] ${e.message}`);
            // 出错时也返回成功，避免程序崩溃
            return 1;
        }
    }, 'int', ['pointer']);
}

/**
 * 监控特定文件API
 * @param {string} apiName - API名称 (如 "CreateFileW", "WriteFile", "ReadFile" 等)
 * @param {string} filePath - 文件路径关键字
 * @param {boolean} monitorReturn - 是否监控返回值 (默认: true)
 */
function monitorFileApi(apiName, filePath, monitorReturn = true) {
    console.log(`[+] Monitoring file API: ${apiName} for path: "${filePath}"`);
    
    // 为DeleteFile API使用替换方式，阻止删除但返回成功
    if (apiName === "DeleteFileW" || apiName === "DeleteFileA") {
        try {
            const module = Process.getModuleByName("kernel32.dll");
            const apiAddress = module.getExportByName(apiName);
            
            if (apiAddress) {
                const replacement = createDeleteFileReplacement(apiName, filePath);
                Interceptor.replace(apiAddress, replacement);
                console.log(`[+] Replaced ${apiName} with custom implementation`);
            } else {
                console.log(`[-] API ${apiName} not found in kernel32.dll`);
            }
        } catch (e) {
            console.log(`[+] Error replacing ${apiName}: ${e.message}`);
        }
    } else {
        // 其他API使用正常的监控方式
        const onEnter = createFileOnEnter(apiName, filePath);
        const onLeave = monitorReturn ? createFileOnLeave(apiName) : null;
        monitorApi("kernel32.dll", apiName, onEnter, onLeave);
    }
}

/**
 * 监控多个文件API
 * @param {string[]} apiNames - API名称数组
 * @param {string} filePath - 文件路径关键字
 */
function monitorFileApis(apiNames, filePath) {
    console.log("=".repeat(70));
    console.log(`Starting File System Monitor for path: "${filePath}"`);
    console.log("=".repeat(70));
    
    apiNames.forEach(apiName => {
        monitorFileApi(apiName, filePath);
    });
    
    console.log("[✓] All file API monitors initialized");
    console.log("=".repeat(70));
}
