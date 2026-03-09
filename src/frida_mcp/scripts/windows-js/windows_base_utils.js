// Windows API监控脚本
function monitorApi(moduleName, apiName) {
    console.log(`[+] Monitoring ${moduleName}!${apiName}`);

    try {
        const module = Process.getModuleByName(moduleName);
        if (!module) {
            console.log(`[-] Module ${moduleName} not found`);
            return;
        }

        const apiAddress = module.getExportByName(apiName);
        if (!apiAddress) {
            console.log(`[-] API ${apiName} not found in ${moduleName}`);
            return;
        }

        Interceptor.attach(apiAddress, {
            onEnter: function(args) {
                try {
                    console.log(`[+] ${apiName} called`);
                    
                    // 打印参数
                    for (let i = 0; i < 6; i++) {
                        if (args[i]) {
                            console.log(`[+] arg[${i}]: 0x${args[i].toString(16)}`);
                        }
                    }
                    
                    // 保存参数用于onLeave
                    this.args = [];
                    for (let i = 0; i < 6; i++) {
                        this.args[i] = args[i];
                    }
                } catch (e) {
                    console.log(`[+] Error in onEnter: ${e.message}`);
                }
            },
            onLeave: function(retval) {
                try {
                    console.log(`[+] ${apiName} returned: 0x${retval.toString(16)}`);
                    
                    // 如果返回的是字符串，打印字符串内容
                    if (retval.toInt32() > 0) {
                        try {
                            const str = Memory.readUtf8String(ptr(retval.toInt32()));
                            console.log(`[+] Return string: ${str}`);
                        } catch (e) {
                            // 不是字符串，忽略
                        }
                    }
                } catch (e) {
                    console.log(`[+] Error in onLeave: ${e.message}`);
                }
            }
        });
        
        console.log(`[+] Successfully attached to ${moduleName}!${apiName}`);
    } catch (e) {
        console.log(`[+] Error setting up API monitor: ${e.message}`);
    }
}