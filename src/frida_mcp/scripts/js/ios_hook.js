// iOS Hook Template
if (ObjC.available) {
    var targetClass = "{{target_class}}";
    var targetMethod = "{{target_method}}";
    
    console.log("[+] Hooking " + targetClass + ":" + targetMethod);
    
    var hook = ObjC.classes[targetClass][targetMethod];
    Interceptor.attach(hook.implementation, {
        onEnter: function(args) {
            console.log("[+] " + targetClass + ":" + targetMethod + " called");
            
            // 打印参数
            for (var i = 0; i < {{arg_count}}; i++) {
                console.log("[+] arg[" + i + "]: " + new ObjC.Object(args[i]));
            }
        },
        onLeave: function(retval) {
            console.log("[+] Return value: " + new ObjC.Object(retval));
        }
    });
}