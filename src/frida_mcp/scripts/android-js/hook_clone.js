function hook_clone() {
    var clone = Module.findExportByName('libc.so', 'clone');

    Interceptor.attach(clone, {
        onEnter: function (args) {
            console.log("═══ Clone Called ═══");
            console.log("args[0] (wrapper):", args[0]);  // __pthread_start
            console.log("args[1] (stack)  :", args[1]);
            console.log("args[2] (flags)  :", args[2]);
            console.log("args[3] (tls)    :", args[3]);  //// 线程局部存储（TLS）

            if (args[3] != 0) {
                try {
                    // 读取真正的线程函数
                    var real_func = args[3].add(96).readPointer();
                    var module = Process.findModuleByAddress(real_func);

                    if (module) {
                        var offset = real_func.sub(module.base);
                        console.log(" 真正的线程函数:");
                        console.log("   SO名称:", module.name);
                        console.log("   函数地址:", real_func);
                        console.log("   偏移:", ptr(offset));


                        if (module.name.includes("DexHelper")) {
                            console.log(" 检测到目标so!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
                        }
                    }
                } catch (e) {
                    console.log("解析失败:", e);
                }
            }
        }
    });
}

setImmediate(hook_clone);