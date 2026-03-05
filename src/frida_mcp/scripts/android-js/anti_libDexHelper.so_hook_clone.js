function hook_clone() {
    var clone = Module.findExportByName('libc.so', 'clone');
    Interceptor.attach(clone, {
        onEnter: function (args) {
            //只有当 args[3] 不为 NULL 时，才说明上层确实把 “线程控制块指针” 传进来了
            if (args[3] != 0) {
                var thread_func_addr = args[3].add(96).readPointer()        // 真正的用户线程函数地址
                var module = Process.findModuleByAddress(thread_func_addr); // 根据线程函数地址 addr，找它属于哪个模块
                var offset = (thread_func_addr - module.base);              // 获取相对于 base 的偏移
                console.log(`[+]libc.so clone thread func: ${module.name}+0x${offset.toString(16)}`);
            }
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
                    hook_clone();            // hook clone打印检测线程正常运行
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