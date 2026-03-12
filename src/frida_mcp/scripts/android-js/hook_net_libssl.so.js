/**
 * Network Hook - SSL/TCP Traffic Interception
 * Hook libssl.so and libc.so network functions
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_net_libssl.so.js
 * Frida 17 Compatible
 */

// Configuration
var HookNet_CONFIG = {
    hookSsl: true,
    hookTcp: true,
    printRequestLine: true,
    targetFilter: ""
};

/**
 * Parse HTTP headers and extract request info
 */
function HookNet_parseHttpRequest(buffer, size) {
    var bytes = ptr(buffer).readByteArray(4);
    var hexHeader = FridaUtils.bytesToHex(bytes).toLowerCase();
    
    var method = FridaUtils.detectHttpMethod(hexHeader);
    if (!method) return null;
    
    var arr = new Uint8Array(ptr(buffer).readByteArray(size));
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] === 0x0d && arr[i + 1] === 0x0a && 
            arr[i + 2] === 0x0d && arr[i + 3] === 0x0a) {
            
            var headers = ptr(buffer).readUtf8String(i);
            var contentLength = FridaUtils.getContentLength(headers);
            var realLen = contentLength === null ? i : i + 4 + contentLength;
            
            return {
                headers: headers,
                body: FridaUtils.readUtf8StringSafe(ptr(buffer), realLen)
            };
        }
    }
    return null;
}

/**
 * Parse HTTP response
 */
function HookNet_parseHttpResponse(buffer, size, retval) {
    var bytes = ptr(buffer).readByteArray(4);
    var hexHeader = FridaUtils.bytesToHex(bytes).toLowerCase();
    
    if (!FridaUtils.isHttpResponse(hexHeader)) return null;
    
    var arr = new Uint8Array(ptr(buffer).readByteArray(size));
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] === 0x0d && arr[i + 1] === 0x0a && 
            arr[i + 2] === 0x0d && arr[i + 3] === 0x0a) {
            
            var headers = ptr(buffer).readUtf8String(i);
            var hasChunked = FridaUtils.hasTransferEncodingChunked(headers);
            
            return {
                headers: headers,
                hasChunked: hasChunked,
                headEnd: i
            };
        }
    }
    return null;
}

/**
 * Check if response chunk is final
 */
function HookNet_isFinalChunk(buffer, size) {
    if (size < 5) return false;
    var bytes = ptr(buffer).add(size - 5).readByteArray(5);
    var arr = new Uint8Array(bytes);
    return arr[0] === 0x30 && arr[1] === 0x0d && arr[2] === 0x0a && 
           arr[3] === 0x0d && arr[4] === 0x0a;
}

/**
 * Hook SSL functions
 */
function HookNet_hookSslFunctions() {
    var sslWritePtr = Process.getModuleByName('libssl.so').getExportByName('SSL_write');
    var sslReadPtr = Process.getModuleByName('libssl.so').getExportByName('SSL_read');
    var sslGetFdPtr = Process.getModuleByName('libssl.so').getExportByName('SSL_get_rfd');
    var sslGetFdFunc = new NativeFunction(sslGetFdPtr, 'int', ['pointer']);
    
    console.log("[SSL] SSL_write:", sslWritePtr, ", SSL_read:", sslReadPtr);
    
    var requestMap = new Map();
    var chunkMap = new Map();
    
    Interceptor.attach(sslWritePtr, {
        onEnter: function (args) {
            this.sslPtr = args[0];
            this.buff = args[1];
            this.size = args[2];
        },
        onLeave: function (retval) {
            var result = HookNet_parseHttpRequest(this.buff, this.size.toInt32());
            if (result) {
                requestMap.set(this.sslPtr.toString(), result.body);
                if (HookNet_CONFIG.printRequestLine) {
                    var firstLine = result.body.substring(0, result.body.indexOf('\n'));
                    console.log("[SSL Request] " + firstLine.trim());
                }
            }
        }
    });
    
    Interceptor.attach(sslReadPtr, {
        onEnter: function (args) {
            this.sslPtr = args[0];
            this.buff = args[1];
            this.size = args[2];
        },
        onLeave: function (retval) {
            var fdStr = this.sslPtr.toString();
            var retSize = retval.toInt32();
            
            if (chunkMap.has(fdStr)) {
                if (retSize > 0) {
                    var chunk = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, chunkMap.get(fdStr) + chunk);
                    
                    if (HookNet_isFinalChunk(this.buff, retSize)) {
                        FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                    }
                } else {
                    FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                }
                return;
            }
            
            var result = HookNet_parseHttpResponse(this.buff, this.size.toInt32(), retval);
            if (result) {
                if (HookNet_CONFIG.printRequestLine) {
                    var firstLine = result.headers.substring(0, result.headers.indexOf('\n'));
                    console.log("[SSL Response] " + firstLine.trim());
                }
                
                if (result.hasChunked) {
                    var content = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, content);
                    
                    if (HookNet_isFinalChunk(this.buff, retSize)) {
                        FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                    }
                } else {
                    var content = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, content);
                    FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                }
            }
        }
    });
}

/**
 * Hook TCP functions
 */
function HookNet_hookTcpFunctions() {
    var sendtoPtr = Process.getModuleByName('libc.so').getExportByName('sendto');
    var recvfromPtr = Process.getModuleByName('libc.so').getExportByName('recvfrom');
    
    console.log("[TCP] sendto:", sendtoPtr, ", recvfrom:", recvfromPtr);
    
    var requestMap = new Map();
    var chunkMap = new Map();
    
    Interceptor.attach(sendtoPtr, {
        onEnter: function (args) {
            this.fd = args[0];
            this.buff = args[1];
            this.size = args[2];
        },
        onLeave: function (retval) {
            var result = HookNet_parseHttpRequest(this.buff, this.size.toInt32());
            if (result) {
                requestMap.set(this.fd.toString(), result.body);
                if (HookNet_CONFIG.printRequestLine) {
                    var firstLine = result.body.substring(0, result.body.indexOf('\n'));
                    console.log("[TCP Request] " + firstLine.trim());
                }
            }
        }
    });
    
    Interceptor.attach(recvfromPtr, {
        onEnter: function (args) {
            this.fd = args[0];
            this.buff = args[1];
            this.size = args[2];
        },
        onLeave: function (retval) {
            var fdStr = this.fd.toString();
            var retSize = retval.toInt32();
            
            if (chunkMap.has(fdStr)) {
                if (retSize > 0) {
                    var chunk = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, chunkMap.get(fdStr) + chunk);
                    
                    if (HookNet_isFinalChunk(this.buff, retSize)) {
                        FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                    }
                } else {
                    FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                }
                return;
            }
            
            var result = HookNet_parseHttpResponse(this.buff, this.size.toInt32(), retval);
            if (result) {
                if (HookNet_CONFIG.printRequestLine) {
                    var firstLine = result.headers.substring(0, result.headers.indexOf('\n'));
                    console.log("[TCP Response] " + firstLine.trim());
                }
                
                if (result.hasChunked) {
                    var content = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, content);
                    
                    if (HookNet_isFinalChunk(this.buff, retSize)) {
                        FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                    }
                } else {
                    var content = FridaUtils.readUtf8StringSafe(ptr(this.buff), retSize);
                    chunkMap.set(fdStr, content);
                    FridaUtils.printHttpResult(requestMap, chunkMap, fdStr);
                }
            }
        }
    });
}

/**
 * Main entry point
 */
function HookNet_main() {
    Java.perform(function () {
        console.log("[*] Network Hooks Started");
        
        if (HookNet_CONFIG.hookSsl) {
            try {
                HookNet_hookSslFunctions();
                console.log("[+] SSL hooks installed");
            } catch (e) {
                console.log("[-] SSL hooks failed:", e.message);
            }
        }
        
        if (HookNet_CONFIG.hookTcp) {
            try {
                HookNet_hookTcpFunctions();
                console.log("[+] TCP hooks installed");
            } catch (e) {
                console.log("[-] TCP hooks failed:", e.message);
            }
        }
        
        console.log("[*] All network hooks installed");
    });
}

setImmediate(HookNet_main);
