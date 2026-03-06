// Windows文件监控脚本
function monitorFile() {
    const filePath = "{{file_path}}";
    console.log(`[+] Monitoring file: ${filePath}`);

    // Hook CreateFileW
    const CreateFileW = Module.getExportByName('kernel32.dll', 'CreateFileW');
    Interceptor.attach(CreateFileW, {
        onEnter: function(args) {
            const lpFileName = args[0];
            const dwDesiredAccess = args[1];
            const dwShareMode = args[2];
            const lpSecurityAttributes = args[3];
            const dwCreationDisposition = args[4];
            const dwFlagsAndAttributes = args[5];
            const hTemplateFile = args[6];
            
            const fileName = Memory.readUtf16String(lpFileName);
            
            if (fileName.includes(filePath)) {
                console.log(`[+] CreateFileW called for: ${fileName}`);
                console.log(`[+] Desired access: 0x${dwDesiredAccess.toString(16)}`);
                console.log(`[+] Creation disposition: 0x${dwCreationDisposition.toString(16)}`);
            }
        }
    });

    // Hook WriteFile
    const WriteFile = Module.getExportByName('kernel32.dll', 'WriteFile');
    Interceptor.attach(WriteFile, {
        onEnter: function(args) {
            const hFile = args[0];
            const lpBuffer = args[1];
            const nNumberOfBytesToWrite = args[2];
            const lpNumberOfBytesWritten = args[3];
            const lpOverlapped = args[4];
            
            console.log("[+] WriteFile called");
            console.log(`[+] Bytes to write: ${nNumberOfBytesToWrite.toInt32()}`);
            
            // 读取写入的数据
            if (nNumberOfBytesToWrite.toInt32() > 0 && nNumberOfBytesToWrite.toInt32() < 1024) {
                try {
                    const data = Memory.readUtf8String(lpBuffer, nNumberOfBytesToWrite.toInt32());
                    console.log(`[+] Data: ${data}`);
                } catch (e) {
                    console.log(`[+] Binary data (length: ${nNumberOfBytesToWrite.toInt32()})`);
                }
            }
        }
    });
}

// 执行监控
monitorFile();