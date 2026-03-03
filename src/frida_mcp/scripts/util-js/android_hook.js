// Android Hook Template
Java.perform(function() {
    var targetClass = "{{target_class}}";
    var targetMethod = "{{target_method}}";
    
    console.log("[+] Hooking " + targetClass + "." + targetMethod);
    
    var clazz = Java.use(targetClass);
    clazz[targetMethod].implementation = function() {
        console.log("[+] " + targetClass + "." + targetMethod + " called");
        
        // 打印参数
        for (var i = 0; i < arguments.length; i++) {
            console.log("[+] arg[" + i + "]: " + safeStringify(arguments[i]));
        }
        
        // 调用原始方法
        var result = this[targetMethod].apply(this, arguments);
        console.log("[+] Result: " + safeStringify(result));
        
        return result;
    };
});