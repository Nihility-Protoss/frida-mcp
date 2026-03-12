/**
 * Anti libDexHelper - Main Bypass Script
 * Bypass detection and hook clone for libDexHelper.so
 */

function AntiMain_hook_clone() {
    var clone = Module.findExportByName('libc.so', 'clone');
    Interceptor.attach(clone, {
        onEnter: function (args) {
            if (args[3] != 0) {
                var thread_func_addr = args[3].add(96).readPointer();
                var module = Process.findModuleByAddress(thread_func_addr);
                var offset = (thread_func_addr - module.base);
                console.log(`[+]libc.so clone thread func: ${module.name}+0x${offset.toString(16)}`);
            }
        }
    });
}

function AntiMain_nopFunc(addr) {
    Memory.protect(addr, 4, 'rwx');
    var writer = new Arm64Writer(addr);
    writer.putRet();
    writer.flush();
    writer.dispose();
    console.log("nop " + addr + " success");
}

function AntiMain_bypass_detect() {
    var base = Module.findBaseAddress("libDexHelper.so");
    var hook_addr_list = {{hook_addr_list}};
    for (const hookAddrListKey in hook_addr_list) {
        AntiMain_nopFunc(base.add(hookAddrListKey));
    }
}

function AntiMain_hook_dlopen() {
    const funcName = "android_dlopen_ext";
    const libc = Module.findBaseAddress("libc.so");
    var funcPtr = Module.findExportByName(null, funcName);

    if (funcPtr !== null && funcPtr !== undefined) {
        console.log(`[*] Hooking ${funcName} at libc.so!0x${(funcPtr - libc.base).toString(16)}`);

        Interceptor.attach(funcPtr, {
            onEnter: function (args) {
                this.pathPtr = args[0];
                if (this.pathPtr !== null && this.pathPtr !== undefined) {
                    try {
                        var path = this.pathPtr.readCString();
                        console.log("\x1b[36m[dlopen] \x1b[0m" + path);
                        if (path.indexOf("libDexHelper.so") !== -1) {
                            this.isTarget = true;
                        }
                    } catch (e) {
                        console.log("[!] Error reading path string");
                    }
                }
            },
            onLeave: function (retval) {
                if (this.isTarget) {
                    AntiMain_hook_clone();
                    AntiMain_bypass_detect();
                }
            }
        });
    } else {
        console.log("[-] Warning: " + funcName + " not found in exports.");
    }
}

function AntiMain_main() {
    AntiMain_hook_dlopen();
}

setImmediate(AntiMain_main);
