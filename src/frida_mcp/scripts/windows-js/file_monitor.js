// Windows文件监控脚本
var filePath = "{{file_path}}";

console.log("[+] Monitoring file: " + filePath);

// Hook CreateFileW
var CreateFileW = Module.getExportByName('kernel32.dll', 'CreateFileW');
Interceptor.attach(CreateFileW, {
    onEnter: function(args) {
        var lpFileName = args[0];
        var dwDesiredAccess = args[1];
        var dwShareMode = args[2];
        var lpSecurityAttributes = args[3];
        var dwCreationDisposition = args[4];
        var dwFlagsAndAttributes = args[5];
        var hTemplateFile = args[6];
        
        var fileName = Memory.readUtf16String(lpFileName);
        
        if (fileName.includes(filePath)) {
            console.log("[+] CreateFileW called for: " + fileName);
            console.log("[+] Desired access: 0x" + dwDesiredAccess.toString(16));
            console.log("[+] Creation disposition: 0x" + dwCreationDisposition.toString(16));
        }
    }
});

// Hook WriteFile
var WriteFile = Module.getExportByName('kernel32.dll', 'WriteFile');
Interceptor.attach(WriteFile, {
    onEnter: function(args) {
        var hFile = args[0];
        var lpBuffer = args[1];
        var nNumberOfBytesToWrite = args[2];
        var lpNumberOfBytesWritten = args[3];
        var lpOverlapped = args[4];
        
        console.log("[+] WriteFile called");
        console.log("[+] Bytes to write: " + nNumberOfBytesToWrite.toInt32());
        
        // 读取写入的数据
        if (nNumberOfBytesToWrite.toInt32() > 0 && nNumberOfBytesToWrite.toInt32() < 1024) {
            try {
                var data = Memory.readUtf8String(lpBuffer, nNumberOfBytesToWrite.toInt32());
                console.log("[+] Data: " + data);
            } catch (e) {
                console.log("[+] Binary data (length: " + nNumberOfBytesToWrite.toInt32() + ")");
            }
        }
    }
});