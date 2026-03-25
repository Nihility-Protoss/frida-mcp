// Windows文件监控API - 优化版本
// 模板变量：
//   {{file_path}} - 要监控的文件路径关键字（可以为空，监控所有路径）
//   {{api_name}} - 要监控的文件API名称 (如 CreateFileW, WriteFile, ReadFile 等)

// 确保 windows_base_utils.js 已加载

/**
 * 文件访问标志 (dwDesiredAccess)
 */
const FILE_ACCESS_FLAGS = {
    0x80000000: "GENERIC_READ",
    0x40000000: "GENERIC_WRITE",
    0x20000000: "GENERIC_EXECUTE",
    0x10000000: "GENERIC_ALL",
    0x00100000: "SYNCHRONIZE",
    0x00080000: "WRITE_OWNER",
    0x00040000: "WRITE_DAC",
    0x00020000: "READ_CONTROL",
    0x00010000: "DELETE",
    0x00000100: "FILE_WRITE_ATTRIBUTES",
    0x00000080: "FILE_READ_ATTRIBUTES",
    0x00000040: "FILE_DELETE_CHILD",
    0x00000020: "FILE_EXECUTE",
    0x00000010: "FILE_WRITE_EA",
    0x00000008: "FILE_READ_EA",
    0x00000004: "FILE_APPEND_DATA",
    0x00000002: "FILE_WRITE_DATA",
    0x00000001: "FILE_READ_DATA",
    0xC0000000: "GENERIC_READ_WRITE",
    0x120089: "FILE_GENERIC_READ",
    0x120116: "FILE_GENERIC_WRITE",
    0x1200A0: "FILE_GENERIC_EXECUTE",
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
 */
function parseFileCreation(creationFlags) {
    return FILE_CREATION_FLAGS[creationFlags] || `0x${creationFlags.toString(16)}`;
}

/**
 * 文件句柄追踪表
 * key: handle (string), value: {fileName, accessFlags, creationDisposition, operations: [], timestamp}
 */
const fileHandleMap = new Map();

/**
 * 记录文件操作
 */
function recordFileOperation(handle, operation, details) {
    const handleStr = handle.toString();
    const fileInfo = fileHandleMap.get(handleStr);
    if (fileInfo) {
        fileInfo.operations.push({
            api: operation,
            details: details,
            timestamp: Date.now()
        });
        fileHandleMap.set(handleStr, fileInfo);
        return fileInfo;
    }
    return null;
}

/**
 * 输出文件完整操作日志
 */
function outputFileLog(handle, reason) {
    const handleStr = handle.toString();
    const fileInfo = fileHandleMap.get(handleStr);
    if (!fileInfo) return;

    // 如果没有操作记录且是正常关闭，不输出日志
    if (fileInfo.operations.length === 0 && reason === "closed") {
        fileHandleMap.delete(handleStr);
        return;
    }

    // 输出文件操作摘要（精简为两行）
    const ops = fileInfo.operations.map(op => `${op.api}${op.details ? `(${op.details})` : ''}`).join(' → ');
    console.log(`[FILE] ${fileInfo.fileName}\n      Access: ${parseFileAccess(fileInfo.accessFlags)} | Creation: ${parseFileCreation(fileInfo.creationDisposition)} | Ops: ${ops || 'none'} | Result: ${reason}`);

    // 清理记录
    fileHandleMap.delete(handleStr);
}

/**
 * 创建文件API监控的通用onEnter回调
 */
function createFileOnEnter(apiName, filePath) {
    return function (args) {
        let fileName = "";
        let destFileName = "";
        let accessFlags = 0;
        let creationDisposition = 0;
        let buffer = ptr(0);
        let bytesToReadWrite = 0;
        let handle = ptr(0);

        const isWide = apiName.endsWith('W');

        switch (apiName) {
            // ── 创建/打开文件 ─────────────────────────────────────
            case "CreateFileW":
            case "CreateFileA":
                fileName = safeReadString(safeArg(args, 0), isWide);
                accessFlags = safeToUInt32(safeArg(args, 1));
                creationDisposition = safeToUInt32(safeArg(args, 4));
                break;

            // ── 读取文件 ─────────────────────────────────────────
            case "ReadFile":
                handle = safeArg(args, 0);
                buffer = safeArg(args, 1);
                bytesToReadWrite = safeToUInt32(safeArg(args, 2));
                break;

            // ── 写入文件 ─────────────────────────────────────────
            case "WriteFile":
                handle = safeArg(args, 0);
                buffer = safeArg(args, 1);
                bytesToReadWrite = safeToUInt32(safeArg(args, 2));
                break;

            // ── 删除文件 ─────────────────────────────────────────
            case "DeleteFileW":
            case "DeleteFileA":
                fileName = safeReadString(safeArg(args, 0), isWide);
                break;

            // ── 移动/重命名文件 ──────────────────────────────────
            case "MoveFileW":
            case "MoveFileA":
            case "MoveFileExW":
            case "MoveFileExA":
                fileName = safeReadString(safeArg(args, 0), isWide);
                destFileName = safeReadString(safeArg(args, 1), isWide);
                break;

            // ── 复制文件 ─────────────────────────────────────────
            case "CopyFileW":
            case "CopyFileA":
            case "CopyFileExW":
            case "CopyFileExA":
                fileName = safeReadString(safeArg(args, 0), isWide);
                destFileName = safeReadString(safeArg(args, 1), isWide);
                break;

            // ── 关闭句柄 ─────────────────────────────────────────
            case "CloseHandle":
                handle = safeArg(args, 0);
                break;

            // ── 默认 ─────────────────────────────────────────────
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

        // 保存数据供onLeave使用
        this.fileData = {
            apiName,
            fileName,
            destFileName,
            accessFlags,
            creationDisposition,
            buffer,
            bytesToReadWrite,
            handle,
            isTarget
        };
    };
}

/**
 * 创建文件API监控的通用onLeave回调
 */
function createFileOnLeave(apiName) {
    return function (retval) {
        try {
            const data = this.fileData;
            if (!data) return;

            let success = false;
            let handle = ptr(0);

            switch (apiName) {
                case "CreateFileW":
                case "CreateFileA":
                    success = !retval.isNull() && retval.toInt32() !== -1;
                    if (success) {
                        handle = retval;
                        // 记录句柄映射
                        fileHandleMap.set(handle.toString(), {
                            fileName: data.fileName,
                            accessFlags: data.accessFlags,
                            creationDisposition: data.creationDisposition,
                            operations: [],
                            timestamp: Date.now()
                        });
                    }
                    break;

                case "ReadFile":
                    success = retval.toInt32() !== 0;
                    if (success && data.handle) {
                        const fileInfo = recordFileOperation(data.handle, "ReadFile", `${data.bytesToReadWrite} bytes`);
                        if (fileInfo) console.log(`[FILE] ReadFile | ${fileInfo.fileName} | ${data.bytesToReadWrite} bytes`);
                    }
                    break;

                case "WriteFile":
                    success = retval.toInt32() !== 0;
                    if (success && data.handle) {
                        const fileInfo = recordFileOperation(data.handle, "WriteFile", `${data.bytesToReadWrite} bytes`);
                        if (fileInfo) console.log(`[FILE] WriteFile | ${fileInfo.fileName} | ${data.bytesToReadWrite} bytes`);
                    }
                    break;

                case "CloseHandle":
                    handle = data.handle;
                    if (!handle.isNull()) {
                        const fileInfo = fileHandleMap.get(handle.toString());
                        if (fileInfo) {
                            console.log(`[FILE] CloseHandle | ${fileInfo.fileName} | handle closed`);
                            fileHandleMap.delete(handle.toString());
                        }
                    }
                    break;

                case "DeleteFileW":
                case "DeleteFileA":
                    success = retval.toInt32() !== 0;
                    if (success && data.isTarget) {
                        console.log(`[FILE] DeleteFile: ${data.fileName} - SUCCESS`);
                    }
                    break;

                case "MoveFileW":
                case "MoveFileA":
                case "MoveFileExW":
                case "MoveFileExA":
                    success = retval.toInt32() !== 0;
                    if (success && data.isTarget) {
                        console.log(`[FILE] MoveFile: ${data.fileName} -> ${data.destFileName}`);
                    }
                    break;

                case "CopyFileW":
                case "CopyFileA":
                case "CopyFileExW":
                case "CopyFileExA":
                    success = retval.toInt32() !== 0;
                    if (success && data.isTarget) {
                        console.log(`[FILE] CopyFile: ${data.fileName} -> ${data.destFileName}`);
                    }
                    break;
            }
        } catch (e) {
            console.log(`[${apiName} onLeave Error] ${e.message}`);
        }
    };
}

/**
 * 创建DeleteFile API的替换函数，阻止删除但返回成功
 */
function createDeleteFileReplacement(apiName, filePath) {
    return new NativeCallback(function (lpFileName) {
        try {
            const isWide = apiName.endsWith('W');
            const fileName = safeReadString(ptr(lpFileName), isWide);

            const isTarget = isTargetPath(filePath, fileName);

            if (isTarget) {
                console.log(`[BLOCKED] ${apiName} ${fileName} - Deletion prevented, returning success`);
                return 1;
            } else {
                const module = Process.getModuleByName("kernel32.dll");
                const originalFunc = module.getExportByName(apiName);
                const original = new NativeFunction(originalFunc, 'int', ['pointer']);
                return original(lpFileName);
            }
        } catch (e) {
            console.log(`[${apiName} Error] ${e.message}`);
            return 1;
        }
    }, 'int', ['pointer']);
}

/**
 * 监控特定文件API
 */
function monitorFileApi(apiName, filePath, monitorReturn = true) {
    console.log(`[+] [M] file API: ${apiName} for path: "${filePath}"`);

    if (apiName === "DeleteFileW" || apiName === "DeleteFileA") {
        try {
            const module = Process.getModuleByName("kernel32.dll");
            const apiAddress = module.getExportByName(apiName);

            if (apiAddress) {
                const replacement = createDeleteFileReplacement(apiName, filePath);
                Interceptor.replace(apiAddress, replacement);
                console.log(`[+] [R] ${apiName} with custom implementation`);
            } else {
                console.log(`[-] API ${apiName} not found in kernel32.dll`);
            }
        } catch (e) {
            console.log(`[+] Error replacing ${apiName}: ${e.message}`);
        }
    } else {
        const onEnter = createFileOnEnter(apiName, filePath);
        const onLeave = monitorReturn ? createFileOnLeave(apiName) : null;
        monitorApi("kernel32.dll", apiName, onEnter, onLeave);
    }
}
