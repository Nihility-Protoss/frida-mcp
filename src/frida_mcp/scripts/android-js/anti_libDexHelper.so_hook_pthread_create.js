function hook_pthread_create() {
    var pthread_create_addr = Module.findExportByName("libc.so", "pthread_create");
    console.log("pthread_create addr: ", pthread_create_addr);
    Interceptor.attach(pthread_create_addr, {
        onEnter: function (args) {
            var thread_func_addr = args[2];
            var module = Process.findModuleByAddress(thread_func_addr);
            console.log(`pthread_create thread func: ${module.name}+0x${(thread_func_addr - module.base).toString(16)}`);
        }, onLeave: function (retval) {
        }
    });
}

function hook_dlopen() {
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
                        console.log("[!] Error reading path string in " + this.funcName);
                    }
                }
            }, onLeave: function (retval) {
                if (this.isTarget) {
                    hook_pthread_create(); // 如果hook会由于检测libc.so而崩溃
                }
            }
        });
    } else {
        console.log("[-] Warning: " + funcName + " not found in exports.");
    }
}
function main() {
    hook_dlopen();
}
setImmediate(main);