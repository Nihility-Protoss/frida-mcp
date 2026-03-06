function frida_Module_enumerateExports() {
    const moduleName = "{{module_name}}";
    Java.perform(function () {
        const hooks = Module.load(moduleName);
        const Exports = hooks.enumerateExports();
        for(let i = 0; i < Exports.length; i++) {
            //函数类型
            console.log("type:",Exports[i].type);
            //函数名称
            console.log("name:",Exports[i].name);
            //函数地址
            console.log("address:",Exports[i].address);
         }
    });
}
setImmediate(frida_Module_enumerateExports,0);