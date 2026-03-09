// Windows文件监控脚本 - 监控特定文件路径

/**
 * 监控CreateFileW API的使用情况
 * 对特定文件路径有特征输出
 */
function monitorFile_CreateFileW() {
    console.log("[+] Setting up CreateFileW monitor...");

    const kernel32 = Process.getModuleByName('kernel32.dll');
    if (!kernel32) {
        console.log("[-] kernel32.dll module not found");
        return;
    }

    try {
        const CreateFileW = kernel32.getExportByName('CreateFileW');
        if (!CreateFileW) {
            console.log("[-] CreateFileW function not found");
            return;
        }

        Interceptor.attach(CreateFileW, {
            onEnter: function(args) {
                try {
                    const lpFileName = args[0];
                    const dwDesiredAccess = args[1];
                    const dwCreationDisposition = args[4];

                    if (lpFileName && !lpFileName.isNull()) {
                        const fileName = lpFileName.readUtf16String();
                        
                        // 检查是否包含特定文件路径
                        const filePath = "{{file_path}}";
                        const isTarget = filePath !== "" && fileName.includes(filePath);
                        
                        if (isTarget) {
                            console.log("[TARGET FILE] " + "=".repeat(50));
                            console.log(`FILE: ${fileName}`);
                            console.log(`ACCESS: 0x${dwDesiredAccess.toString(16)}`);
                            console.log(`DISPOSITION: 0x${dwCreationDisposition.toString(16)}`);
                            console.log("=".repeat(50));
                        } else {
                            console.log(`[CreateFileW] ${fileName}`);
                        }
                    }
                } catch (e) {
                    console.log(`[CreateFileW Error] ${e.message}`);
                }
            }
        });

        console.log("[✓] CreateFileW monitor active");
    } catch (e) {
        console.log(`[CreateFileW Setup Error] ${e.message}`);
    }
}

/**
 * 监控WriteFile API的使用情况
 * 监控所有文件写入操作
 */
function monitorFile_WriteFile() {
    console.log("[+] Setting up WriteFile monitor...");

    const kernel32 = Process.getModuleByName('kernel32.dll');
    if (!kernel32) {
        console.log("[-] kernel32.dll module not found");
        return;
    }

    try {
        const WriteFile = kernel32.getExportByName('WriteFile');
        if (!WriteFile) {
            console.log("[-] WriteFile function not found");
            return;
        }

        Interceptor.attach(WriteFile, {
            onEnter: function(args) {
                try {
                    const lpBuffer = args[1];
                    const nNumberOfBytesToWrite = args[2];

                    if (lpBuffer && !lpBuffer.isNull()) {
                        const bytesToWrite = nNumberOfBytesToWrite.toInt32();
                        
                        if (bytesToWrite > 0) {
                            let dataPreview = "";
                            try {
                                if (bytesToWrite <= 32) {
                                    dataPreview = lpBuffer.readUtf8String(bytesToWrite);
                                } else {
                                    const preview = lpBuffer.readUtf8String(32);
                                    dataPreview = preview + "...";
                                }
                            } catch (e) {
                                const bytes = lpBuffer.readByteArray(Math.min(bytesToWrite, 16));
                                dataPreview = "[BINARY] " + Array.from(new Uint8Array(bytes))
                                    .map(b => ('0' + b.toString(16)).slice(-2)).join(' ');
                                if (bytesToWrite > 16) dataPreview += "...";
                            }

                            console.log(`[WriteFile] ${bytesToWrite} bytes: ${dataPreview}`);
                        }
                    }
                } catch (e) {
                    console.log(`[WriteFile Error] ${e.message}`);
                }
            }
        });

        console.log("[✓] WriteFile monitor active");
    } catch (e) {
        console.log(`[WriteFile Setup Error] ${e.message}`);
    }
}

/**
 * 主函数：执行所有文件监控
 */
function monitorFile() {
    console.log("=".repeat(60));
    console.log("Starting Windows File System Monitor");
    console.log("=".repeat(60));

    monitorFile_CreateFileW();
    monitorFile_WriteFile();

    console.log("[✓] All file monitors initialized");
    console.log("=".repeat(60));
}

// 执行监控
monitorFile();