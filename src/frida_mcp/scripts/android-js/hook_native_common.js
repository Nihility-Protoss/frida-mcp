/**
 * Common Native Layer Hooks
 * Hook common native functions: SO loading, NewStringUTF, RegisterNatives
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_native_common.js
 * Frida 17 Compatible
 */

// Configuration
var HookNative_CONFIG = {
    monitorSoLoad: true,
    blockSoName: "{{block_so_name}}",
    hookNewStringUTF: true,
    newStringUTFFilter: "{{newstringutf_filter}}",
    newStringUTFLength: 0,
    hookRegisterNatives: true,
    registerNativesTarget: "{{register_target_class}}"
};

/**
 * Monitor SO loading
 */
function HookNative_monitorSo() {
    FridaUtils.hookSoLoad(function (path, retval) {
        if (path) {
            console.log("[SO Load] " + path);
        }
    });
    console.log("[+] SO loading monitor installed");
}

/**
 * Block specific SO
 */
function HookNative_blockSo() {
    if (HookNative_CONFIG.blockSoName && !HookNative_CONFIG.blockSoName.includes("{{")) {
        FridaUtils.blockSoLoad(HookNative_CONFIG.blockSoName);
        console.log("[+] SO block installed for: " + HookNative_CONFIG.blockSoName);
    }
}

/**
 * Hook NewStringUTF
 */
function HookNative_newStringUTF() {
    var filterFunc;
    
    if (HookNative_CONFIG.newStringUTFLength > 0) {
        filterFunc = function (str) {
            return str.length === HookNative_CONFIG.newStringUTFLength;
        };
    } else if (HookNative_CONFIG.newStringUTFFilter && !HookNative_CONFIG.newStringUTFFilter.includes("{{")) {
        filterFunc = function (str) {
            return str.indexOf(HookNative_CONFIG.newStringUTFFilter) !== -1;
        };
    } else {
        filterFunc = function (str) {
            return str.length > 20;
        };
    }
    
    FridaUtils.hookNewStringUTF(filterFunc, function (str, backtrace) {
        console.log("\n[NewStringUTF] String:", str.substring(0, 200));
        console.log("Call Stack:\n" + backtrace);
    });
    
    console.log("[+] NewStringUTF hooked");
}

/**
 * Hook RegisterNatives
 */
function HookNative_registerNatives() {
    if (!HookNative_CONFIG.registerNativesTarget || HookNative_CONFIG.registerNativesTarget.includes("{{")) {
        console.log("[-] RegisterNatives target not configured");
        return;
    }
    
    FridaUtils.hookRegisterNatives(HookNative_CONFIG.registerNativesTarget, function (className, methods) {
        console.log("\n[RegisterNatives] Target class:", className);
        for (var i = 0; i < methods.length; i++) {
            var m = methods[i];
            console.log("  [" + i + "] Java:", m.name, "| Sig:", m.signature);
            console.log("       SO:", m.module, "| Offset:", m.offset);
        }
    });
    
    console.log("[+] RegisterNatives hooked");
}

/**
 * Hook common native functions
 */
function HookNative_commonFuncs() {
    FridaUtils.safeHook("libc.so", "pthread_create", {
        onEnter: function (args) {
            console.log("[pthread_create] Thread creation detected");
        }
    });
    
    FridaUtils.safeHook("libc.so", "open", {
        onEnter: function (args) {
            var path = args[0].readCString();
            if (path && (path.endsWith(".so") || path.endsWith(".dex"))) {
                console.log("[open] " + path);
            }
        }
    });
    
    FridaUtils.safeHook("libc.so", "socket", {
        onLeave: function (retval) {
            console.log("[socket] Created socket fd:", retval.toInt32());
        }
    });
    
    FridaUtils.safeHook("libc.so", "connect", {
        onEnter: function (args) {
            var fd = args[0].toInt32();
            try {
                var sockInfo = FridaUtils.getSocketData(fd);
                console.log("[connect] fd:", fd, sockInfo);
            } catch (e) {}
        }
    });
}

/**
 * Main entry point
 */
function HookNative_main() {
    Java.perform(function () {
        console.log("[*] Common Native Hooks Started");
        
        if (HookNative_CONFIG.monitorSoLoad) {
            HookNative_monitorSo();
        }
        
        HookNative_blockSo();
        
        if (HookNative_CONFIG.hookNewStringUTF) {
            HookNative_newStringUTF();
        }
        
        if (HookNative_CONFIG.hookRegisterNatives) {
            HookNative_registerNatives();
        }
        
        HookNative_commonFuncs();
        
        console.log("[*] All native hooks installed");
    });
}

setImmediate(HookNative_main);
