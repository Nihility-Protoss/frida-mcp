/**
 * Clone System Call Hook
 * Monitor thread creation via clone() system call
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_clone.js
 * Frida 17 Compatible
 */

// Configuration
var HookClone_CONFIG = {
    targetSoName: "{{anti_so_name_tag}}",
    showAllThreads: true
};

/**
 * Hook clone system call
 */
function HookClone_doHook() {
    var clone = Module.findExportByName('libc.so', 'clone');
    if (!clone) {
        console.log("[-] clone() not found in libc.so");
        return;
    }
    
    console.log("[*] Hooking clone() at", clone);
    
    Interceptor.attach(clone, {
        onEnter: function (args) {
            console.log("\n═══ Clone Called ═══");
            console.log("  args[0] (wrapper):", args[0]);
            console.log("  args[1] (stack):  ", args[1]);
            console.log("  args[2] (flags):  ", args[2]);
            console.log("  args[3] (tls):    ", args[3]);
            
            if (args[3] != 0) {
                try {
                    var realFunc = args[3].add(96).readPointer();
                    var moduleInfo = FridaUtils.getModuleInfoByAddress(realFunc);
                    
                    if (moduleInfo) {
                        console.log("  线程函数:");
                        console.log("    SO名称:  ", moduleInfo.name);
                        console.log("    函数地址:", moduleInfo.address);
                        console.log("    偏移:    ", moduleInfo.offset);
                        
                        var shouldShow = HookClone_CONFIG.showAllThreads;
                        if (HookClone_CONFIG.targetSoName && !HookClone_CONFIG.targetSoName.includes("{{")) {
                            if (moduleInfo.name.includes(HookClone_CONFIG.targetSoName)) {
                                console.log("  [!] 检测到目标SO线程!!!!!!!!!!!!!!!!");
                                shouldShow = true;
                            }
                        }
                        
                        if (!shouldShow) {
                            console.log("  (filtered)");
                        }
                    }
                } catch (e) {
                    console.log("  [-] 解析失败:", e.message);
                }
            }
        }
    });
    
    console.log("[+] clone() hooked");
}

/**
 * Main entry point
 */
function HookClone_main() {
    console.log("[*] Clone Hook Started");
    HookClone_doHook();
}

setImmediate(HookClone_main);
