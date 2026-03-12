/**
 * Android Base Utilities for Frida 17
 * Common utility functions for Android hooking
 * 
 * This file provides reusable utility functions that can be used by other scripts.
 * All functions are namespaced under FridaUtils to avoid global conflicts.
 * 
 * Usage: Include this file before other hook scripts:
 *   frida -Uf com.package.name -l android_base_utils.js -l hook_xxx.js
 */

// Create global namespace
var FridaUtils = FridaUtils || {};

// ============================================
// SO Loading Utilities
// ============================================

/**
 * Hook SO loading (dlopen/android_dlopen_ext)
 * @param {Function} callback - function(path, retval)
 */
FridaUtils.hookSoLoad = function(callback) {
    var dlopen = Module.findExportByName(null, "dlopen");
    var android_dlopen_ext = Module.findExportByName(null, "android_dlopen_ext");

    if (dlopen) {
        Interceptor.attach(dlopen, {
            onEnter: function (args) {
                this.path = args[0].readCString();
            },
            onLeave: function (retval) {
                if (this.path) {
                    callback(this.path, retval);
                }
            }
        });
    }

    if (android_dlopen_ext) {
        Interceptor.attach(android_dlopen_ext, {
            onEnter: function (args) {
                this.path = args[0].readCString();
            },
            onLeave: function (retval) {
                if (this.path) {
                    callback(this.path, retval);
                }
            }
        });
    }
};

/**
 * Execute hook function when specific SO is loaded
 * @param {string} soName - SO name to wait for
 * @param {Function} hookFunc - function to execute
 */
FridaUtils.hookSoLoadAndExecute = function(soName, hookFunc) {
    FridaUtils.hookSoLoad(function (path, retval) {
        if (path && path.indexOf(soName) !== -1) {
            console.log("[SO Loaded] " + path);
            hookFunc();
        }
    });
};

/**
 * Block specific SO from loading
 * @param {string} soName - SO name to block
 */
FridaUtils.blockSoLoad = function(soName) {
    var android_dlopen_ext = Module.findExportByName(null, "android_dlopen_ext");
    if (!android_dlopen_ext) return;

    Interceptor.attach(android_dlopen_ext, {
        onEnter: function (args) {
            var path = args[0].readCString();
            if (path && path.indexOf(soName) !== -1) {
                args[0].writeUtf8String("");
                console.log("[Block SO] Blocked: " + soName);
            }
        }
    });
};

// ============================================
// JNI Utilities
// ============================================

/**
 * Find NewStringUTF symbol in libart.so
 * @returns {NativePointer|null}
 */
FridaUtils.findNewStringUTF = function() {
    var artModule = Process.findModuleByName("libart.so");
    if (!artModule) return null;

    var symbols = artModule.enumerateSymbols();
    for (var i = 0; i < symbols.length; i++) {
        var symbol = symbols[i];
        if (symbol.name.indexOf("NewStringUTF") >= 0 && 
            symbol.name.indexOf("CheckJNI") < 0) {
            return symbol.address;
        }
    }
    return null;
};

/**
 * Hook NewStringUTF with filter
 * @param {Function} filterFunc - function(str) returns boolean
 * @param {Function} callback - function(str, backtrace)
 */
FridaUtils.hookNewStringUTF = function(filterFunc, callback) {
    var addr = FridaUtils.findNewStringUTF();
    if (!addr) {
        console.log("[-] NewStringUTF not found");
        return;
    }

    Interceptor.attach(addr, {
        onEnter: function (args) {
            var cString = args[1];
            var dataString = cString.readCString();
            if (dataString && filterFunc(dataString)) {
                var backtrace = Thread.backtrace(this.context, Backtracer.ACCURATE)
                    .map(DebugSymbol.fromAddress)
                    .join('\n');
                callback(dataString, backtrace);
            }
        }
    });
};

/**
 * Find RegisterNatives symbol in libart.so
 * @returns {NativePointer|null}
 */
FridaUtils.findRegisterNatives = function() {
    var symbols = Module.enumerateSymbolsSync("libart.so");
    for (var i = 0; i < symbols.length; i++) {
        var symbol = symbols[i];
        if (symbol.name.indexOf("art") >= 0 &&
            symbol.name.indexOf("JNI") >= 0 &&
            symbol.name.indexOf("RegisterNatives") >= 0 &&
            symbol.name.indexOf("CheckJNI") < 0) {
            return symbol.address;
        }
    }
    return null;
};

/**
 * Hook RegisterNatives for specific class
 * @param {string} targetClass - Full class name to monitor
 * @param {Function} callback - function(methodsArray)
 */
FridaUtils.hookRegisterNatives = function(targetClass, callback) {
    var addr = FridaUtils.findRegisterNatives();
    if (!addr) {
        console.log("[-] RegisterNatives not found");
        return;
    }

    Interceptor.attach(addr, {
        onEnter: function (args) {
            var env = args[0];
            var javaClass = args[1];
            var className = Java.vm.tryGetEnv().getClassName(javaClass);

            if (className === targetClass) {
                var methodsPtr = ptr(args[2]);
                var methodCount = parseInt(args[3]);
                var methods = [];

                for (var i = 0; i < methodCount; i++) {
                    var namePtr = Memory.readPointer(methodsPtr.add(i * Process.pointerSize * 3));
                    var sigPtr = Memory.readPointer(methodsPtr.add(i * Process.pointerSize * 3 + Process.pointerSize));
                    var fnPtr = Memory.readPointer(methodsPtr.add(i * Process.pointerSize * 3 + Process.pointerSize * 2));

                    var name = Memory.readCString(namePtr);
                    var sig = Memory.readCString(sigPtr);
                    var module = Process.findModuleByAddress(fnPtr);
                    var offset = ptr(fnPtr).sub(module.base);

                    methods.push({
                        name: name,
                        signature: sig,
                        address: fnPtr,
                        module: module.name,
                        offset: offset
                    });
                }
                callback(className, methods);
            }
        }
    });
};

// ============================================
// Call Stack Utilities
// ============================================

/**
 * Log Java call stack
 * @param {string} tag - Tag for log
 * @param {number} maxLines - Max stack lines (default 20)
 */
FridaUtils.logJavaCallStack = function(tag, maxLines) {
    maxLines = maxLines || 20;
    console.log("\n[+] " + tag + " called!");
    console.log("Call Stack:");
    
    try {
        var Exception = Java.use("java.lang.Exception");
        var exc = Exception.$new();
        var stack = exc.getStackTrace();
        
        for (var i = 0; i < Math.min(stack.length, maxLines); i++) {
            var line = stack[i].toString();
            if (!line.includes("android.") && 
                !line.includes("java.") && 
                !line.includes("dalvik.") && 
                !line.includes("sun.")) {
                console.log("  >>> " + line);
            } else {
                console.log("      " + line);
            }
        }
        exc.$dispose();
    } catch (e) {
        console.log("[-] Failed to get call stack:", e.message);
    }
};

/**
 * Get Java call stack as string
 * @param {number} maxLines - Max stack lines (default 50)
 * @returns {string} Call stack string
 */
FridaUtils.getJavaCallStack = function(maxLines) {
    maxLines = maxLines || 50;
    var result = "";
    
    try {
        var Exception = Java.use("java.lang.Exception");
        var exc = Exception.$new();
        var stack = exc.getStackTrace();
        
        for (var i = 0; i < Math.min(stack.length, maxLines); i++) {
            result += "   " + stack[i].toString() + "\n";
        }
        exc.$dispose();
    } catch (e) {
        result = "[-] Failed to get call stack: " + e.message;
    }
    return result;
};

/**
 * Print Java call stack with formatted output
 * @param {string} str_tag - Tag for output
 */
FridaUtils.showStacks = function(str_tag) {
    console.log("============================= " + str_tag + " Stack start =======================");
    console.log(FridaUtils.getJavaCallStack());
    console.log("============================= " + str_tag + " Stack end =========================\n");
};

/**
 * Log native call stack
 * @param {Object} context - this.context from Interceptor
 */
FridaUtils.logNativeCallStack = function(context) {
    console.log("Native Call Stack:\n", 
        Thread.backtrace(context, Backtracer.ACCURATE)
            .map(DebugSymbol.fromAddress)
            .join('\n'));
};

// ============================================
// Delay Hook Utilities
// ============================================

/**
 * Delay hook execution by time
 * @param {Function} hookFunc - Hook function to execute
 * @param {number} delayMs - Delay in milliseconds (default 1000)
 */
FridaUtils.delayHookByTime = function(hookFunc, delayMs) {
    delayMs = delayMs || 1000;
    setTimeout(function () {
        Java.perform(hookFunc);
    }, delayMs);
};

/**
 * Delay hook execution until SO is loaded
 * @param {string} soName - SO name to wait for
 * @param {Function} hookFunc - Hook function to execute
 */
FridaUtils.delayHookBySoLoad = function(soName, hookFunc) {
    FridaUtils.hookSoLoadAndExecute(soName, function () {
        Java.perform(hookFunc);
    });
};

// ============================================
// Data Conversion Utilities
// ============================================

/**
 * Convert byte array to hex string
 * @param {Array|Uint8Array} bytes - Byte array
 * @returns {string} Hex string
 */
FridaUtils.bytesToHex = function(bytes) {
    var result = "";
    var arr = new Uint8Array(bytes);
    for (var i = 0; i < arr.length; i++) {
        result += ("0" + (arr[i] & 0xFF).toString(16)).slice(-2);
    }
    return result;
};

/**
 * Convert hex string to byte array
 * @param {string} hex - Hex string
 * @returns {Uint8Array} Byte array
 */
FridaUtils.hexToBytes = function(hex) {
    var bytes = [];
    for (var i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    return new Uint8Array(bytes);
};

/**
 * Read UTF-8 string from buffer safely
 * @param {NativePointer} buffer - Buffer pointer
 * @param {number} size - Size to read
 * @returns {string} UTF-8 string
 */
FridaUtils.readUtf8StringSafe = function(buffer, size) {
    try {
        var StringClass = Java.use('java.lang.String');
        var CharsetClass = Java.use('java.nio.charset.Charset');
        var bytes = buffer.readByteArray(size);
        var byteArray = Java.array('byte', new Uint8Array(bytes));
        return StringClass.$new(byteArray, CharsetClass.forName('UTF-8'));
    } catch (e) {
        return buffer.readUtf8String(size);
    }
};

// ============================================
// HTTP/Network Utilities
// ============================================

/**
 * Parse Content-Length from HTTP headers
 * @param {string} responseHeaders - HTTP response headers
 * @returns {number|null} Content length or null
 */
FridaUtils.getContentLength = function(responseHeaders) {
    var regex = /Content-Length:\s*(\d+)/i;
    var match = responseHeaders.match(regex);
    return match && match[1] ? parseInt(match[1], 10) : null;
};

/**
 * Check if response uses chunked transfer encoding
 * @param {string} responseHeaders - HTTP response headers
 * @returns {boolean}
 */
FridaUtils.hasTransferEncodingChunked = function(responseHeaders) {
    var headers = responseHeaders.split('\r\n');
    for (var i = 0; i < headers.length; i++) {
        if (headers[i].toLowerCase().startsWith('transfer-encoding:')) {
            return headers[i].toLowerCase().includes('chunked');
        }
    }
    return false;
};

/**
 * Get socket information
 * @param {number} fd - File descriptor
 * @returns {string} Socket info string
 */
FridaUtils.getSocketData = function(fd) {
    try {
        var socketType = Socket.type(fd);
        if (socketType != null) {
            return "type:" + socketType + ", localAddress:" + JSON.stringify(Socket.localAddress(fd)) + ", peerAddress:" + JSON.stringify(Socket.peerAddress(fd));
        }
    } catch (e) {}
    return "type:null";
};

/**
 * Print HTTP request/response pair
 * @param {Map} requestMap - Map storing requests
 * @param {Map} responseMap - Map storing responses
 * @param {string} key - Key to lookup
 */
FridaUtils.printHttpResult = function(requestMap, responseMap, key) {
    var request = requestMap.get(key);
    if (request) {
        console.log(key + " 请求:");
        console.log(request);
        console.log("\n");
        requestMap.delete(key);
    }

    var response = responseMap.get(key);
    if (response) {
        console.log(key + " 响应:");
        console.log(response);
        responseMap.delete(key);
    }
};

// ============================================
// Module/Address Utilities
// ============================================

/**
 * Get module info by address
 * @param {NativePointer} addr - Address
 * @returns {Object|null} Module info with name, base, offset
 */
FridaUtils.getModuleInfoByAddress = function(addr) {
    var module = Process.findModuleByAddress(addr);
    if (!module) return null;
    
    return {
        name: module.name,
        base: module.base,
        offset: ptr(addr).sub(module.base),
        address: addr
    };
};

/**
 * Export symbol address as string
 * @param {string} moduleName - Module name
 * @param {string} symbolName - Symbol name
 * @returns {string} Address string or "not found"
 */
FridaUtils.getExportAddress = function(moduleName, symbolName) {
    var addr = Module.findExportByName(moduleName, symbolName);
    return addr ? addr.toString() : "not found";
};

// ============================================
// Hook Installation Utilities
// ============================================

/**
 * Safe hook installation with error handling
 * @param {string} moduleName - Target module name
 * @param {string} functionName - Target function name
 * @param {Object} callbacks - onEnter/onLeave callbacks
 * @returns {boolean} Success or failure
 */
FridaUtils.safeHook = function(moduleName, functionName, callbacks) {
    try {
        var addr = Module.findExportByName(moduleName, functionName);
        if (!addr) {
            console.log("[-] " + moduleName + "!" + functionName + " not found");
            return false;
        }
        
        Interceptor.attach(addr, callbacks);
        console.log("[+] " + moduleName + "!" + functionName + " hooked");
        return true;
    } catch (e) {
        console.log("[-] Failed to hook " + moduleName + "!" + functionName + ": " + e.message);
        return false;
    }
};

/**
 * Hook Java method with try-catch wrapper
 * @param {string} className - Full class name
 * @param {string} methodName - Method name
 * @param {Array|string} overloads - Overload signatures (optional)
 * @param {Function} implementation - New implementation
 */
FridaUtils.hookJavaMethod = function(className, methodName, overloads, implementation) {
    try {
        var cls = Java.use(className);
        var method;
        
        if (overloads) {
            if (typeof overloads === 'string') {
                method = cls[methodName].overload(overloads);
            } else {
                method = cls[methodName].overload.apply(null, overloads);
            }
        } else {
            method = cls[methodName];
        }
        
        method.implementation = implementation;
        console.log("[+] " + className + "." + methodName + " hooked");
    } catch (e) {
        console.log("[-] Failed to hook " + className + "." + methodName + ": " + e.message);
    }
};

// ============================================
// Crypto Utilities
// ============================================

/**
 * Detect HTTP method from hex header
 * @param {string} hexHeader - First 4 bytes as hex string
 * @returns {string|null} HTTP method or null
 */
FridaUtils.detectHttpMethod = function(hexHeader) {
    var methods = {
        '504f5354': 'POST',
        '474554': 'GET',
        '505554': 'PUT',
        '44454c455445': 'DELETE',
        '48454144': 'HEAD',
        '4f5054494f4e53': 'OPTIONS',
        '5041544348': 'PATCH',
        '434f4e4e454354': 'CONNECT'
    };
    
    for (var key in methods) {
        if (hexHeader.startsWith(key)) {
            return methods[key];
        }
    }
    return null;
};

/**
 * Check if hex header indicates HTTP response
 * @param {string} hexHeader - First 4 bytes as hex string
 * @returns {boolean}
 */
FridaUtils.isHttpResponse = function(hexHeader) {
    return hexHeader.startsWith('48545450'); // HTTP
};

// ============================================
// Initialization
// ============================================

console.log("[*] FridaUtils (Android Base Utils) loaded");
