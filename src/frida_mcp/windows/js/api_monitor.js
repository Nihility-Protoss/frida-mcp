// Windows API监控脚本
var moduleName = "{{module_name}}";
var apiName = "{{api_name}}";

console.log("[+] Monitoring " + moduleName + "!" + apiName);

var module = Process.getModuleByName(moduleName);
var apiAddress = module.getExportByName(apiName);

Interceptor.attach(apiAddress, {
    onEnter: function(args) {
        console.log("[+] " + apiName + " called");
        
        // 打印参数
        for (var i = 0; i < 6; i++) {
            if (args[i]) {
                console.log("[+] arg[" + i + "]: 0x" + args[i].toString(16));
            }
        }
        
        // 保存参数用于onLeave
        this.args = [];
        for (var i = 0; i < 6; i++) {
            this.args[i] = args[i];
        }
    },
    onLeave: function(retval) {
        console.log("[+] " + apiName + " returned: 0x" + retval.toString(16));
        
        // 如果返回的是字符串，打印字符串内容
        if (retval.toInt32() > 0) {
            try {
                var str = Memory.readUtf8String(ptr(retval.toInt32()));
                console.log("[+] Return string: " + str);
            } catch (e) {
                // 不是字符串，忽略
            }
        }
    }
});